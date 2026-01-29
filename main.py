#!/usr/bin/env python3
"""
AI Client Report Generator - Main Entry Point

Generates PDF reports from client dialogue transcripts using AI analysis.
"""
import argparse
import logging
import sys
from typing import List
from datetime import datetime
from pathlib import Path

import config
from utils.logging_setup import setup_logging
from utils.io import read_text_file
from utils.ai_processor import (
    process_dialog_with_ai,
    extract_design_brief,
    make_image_prompt_from_brief
)
from utils.pdf_generator import generate_pdf_report
from services.openai_client import generate_image

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='AI Client Report Generator - Generate PDF reports from client dialogue transcripts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --input transcripts/meeting_2026.txt
  %(prog)s --input data.txt --output reports/custom_report.pdf
  %(prog)s --no-cache --log-level DEBUG
  %(prog)s --template templates/custom_template.html
        """
    )
    
    parser.add_argument(
        '--input',
        type=Path,
        default=config.FIXTURES_DIR / 'sample_transcript.txt',
        help='Path to transcript file (default: fixtures/sample_transcript.txt)'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='Output PDF path (default: auto-generated in reports/ with timestamp)'
    )
    
    parser.add_argument(
        '--template',
        type=Path,
        default=config.TEMPLATES_DIR / 'report_template.html',
        help='Path to HTML template (default: templates/report_template.html)'
    )

    parser.add_argument(
        '--report-type',
        choices=['client', 'design'],
        default='client',
        help='Report type to generate: client or design (default: client)'
    )
    
    parser.add_argument(
        '--use-cache',
        action='store_true',
        default=True,
        help='Use cached AI responses (default: enabled)'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        default=False,
        help='Force fresh AI request, ignore cache'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default=config.LOG_LEVEL,
        help=f'Logging level (default: {config.LOG_LEVEL})'
    )
    
    args = parser.parse_args()
    
    # Handle cache flags
    if args.no_cache:
        args.use_cache = False
    
    # Generate output path if not specified
    if args.output is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = config.REPORTS_DIR / f'report_{timestamp}.pdf'

    if args.report_type == 'design':
        args.template = config.TEMPLATES_DIR / 'design_report_template.html'
    
    return args


def prompt_select(prompt_title: str, options: List[Path]) -> Path:
    """Prompt user to select a file from a list or enter a custom path."""
    print(f"\n{prompt_title}")
    for idx, option in enumerate(options, start=1):
        print(f"{idx}. {option}")
    print("0. Ввести путь вручную")

    while True:
        choice = input("Выберите номер: ").strip()
        if choice == "0":
            custom_path = input("Введите путь к файлу: ").strip()
            return Path(custom_path)
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(options):
                return options[index - 1]
        print("Некорректный выбор. Повторите.")


def apply_cli_menu(args):
    """Interactive menu to select transcript and template."""
    transcript_options = sorted(config.FIXTURES_DIR.glob("*.txt"))
    template_options = sorted(config.TEMPLATES_DIR.glob("*.html"))

    if not transcript_options:
        print("✗ В fixtures нет .txt файлов для выбора.")
        return args
    if not template_options:
        print("✗ В templates нет .html файлов для выбора.")
        return args

    selected_transcript = prompt_select("Выберите транскрипт:", transcript_options)
    selected_template = prompt_select("Выберите шаблон:", template_options)

    args.input = selected_transcript
    args.template = selected_template
    args.report_type = "design" if selected_template.name == "design_report_template.html" else "client"
    return args


def main():
    """Main application entry point."""
    # Parse arguments
    args = parse_arguments()
    if len(sys.argv) == 1:
        args = apply_cli_menu(args)
    
    # Setup logging
    setup_logging(log_level=args.log_level)
    
    logger.info("=" * 60)
    logger.info("AI Client Report Generator - Starting")
    logger.info("=" * 60)
    logger.info(f"Input file: {args.input}")
    logger.info(f"Output file: {args.output}")
    logger.info(f"Template: {args.template}")
    logger.info(f"Report type: {args.report_type}")
    logger.info(f"Cache enabled: {args.use_cache}")
    logger.info(f"Log level: {args.log_level}")
    
    try:
        # Validate configuration
        config.validate_config()
        
        # Step 1: Read transcript
        print(f"\n[1/3] Чтение транскрипта: {args.input}")
        logger.info("Step 1: Reading transcript file")
        
        if not args.input.exists():
            error_msg = f"Файл не найден: {args.input}"
            logger.error(error_msg)
            print(f"\n✗ ОШИБКА: {error_msg}")
            print(f"Убедитесь, что файл существует и путь указан правильно.")
            return 1
        
        try:
            transcript_text = read_text_file(args.input)
        except UnicodeDecodeError as e:
            error_msg = f"Не удалось прочитать файл (ошибка кодировки): {args.input}"
            logger.error(error_msg, exc_info=True)
            print(f"\n✗ ОШИБКА: {error_msg}")
            print(f"Убедитесь, что файл имеет правильную кодировку (UTF-8).")
            return 1
        except Exception as e:
            error_msg = f"Ошибка чтения файла: {e}"
            logger.error(error_msg, exc_info=True)
            print(f"\n✗ ОШИБКА: {error_msg}")
            return 1
        
        print(f"✓ Прочитано {len(transcript_text)} символов")
        
        # Step 2: Report Data
        image_uri = None
        image_failed = False

        if args.report_type == 'design':
            print(f"\n[2/3] Извлечение дизайн-брифа...")
            logger.info("Step 2: Extracting design brief")

            if args.use_cache:
                print("  (Используется кэширование)")
            else:
                print("  (Кэш отключён, запрос к ИИ)")

            try:
                report_data = extract_design_brief(
                    text=transcript_text,
                    model=config.OPENAI_MODEL,
                    api_key=config.OPENAI_API_KEY,
                    cache_dir=config.CACHE_DIR,
                    use_cache=args.use_cache
                )
                print("✓ Дизайн-бриф извлечён")
                print(f"  Проект: {report_data.project_name}")
            except Exception as e:
                error_msg = f"Ошибка при извлечении дизайн-брифа: {e}"
                logger.error(error_msg, exc_info=True)
                print(f"\n✗ ОШИБКА: {error_msg}")
                return 1

            try:
                logger.info("Step 2.1: Generating image prompt")
                image_prompt = make_image_prompt_from_brief(
                    brief=report_data,
                    model=config.OPENAI_MODEL,
                    api_key=config.OPENAI_API_KEY,
                    cache_dir=config.CACHE_DIR,
                    use_cache=args.use_cache
                )

                logger.info("Step 2.2: Generating image")
                image_path = generate_image(image_prompt)
                image_uri = image_path.as_uri()
                print("✓ Изображение сгенерировано")
            except Exception as e:
                image_failed = True
                logger.error(f"Image generation failed: {e}", exc_info=True)
                print("! image failed")
        else:
            print(f"\n[2/3] Анализ диалога с помощью ИИ...")
            logger.info("Step 2: Processing with AI")

            if args.use_cache:
                print("  (Используется кэширование)")
            else:
                print("  (Кэш отключён, запрос к ИИ)")

            try:
                report_data = process_dialog_with_ai(
                    text=transcript_text,
                    model=config.OPENAI_MODEL,
                    temperature=config.AI_TEMPERATURE,
                    api_key=config.OPENAI_API_KEY,
                    cache_dir=config.CACHE_DIR,
                    use_cache=args.use_cache
                )
                print(f"✓ Анализ завершён")
                print(f"  Клиент: {report_data.client_name}")
                print(f"  Тема: {report_data.topic}")

            except Exception as e:
                error_msg = f"Ошибка при обработке ИИ: {e}"
                logger.error(error_msg, exc_info=True)
                print(f"\n✗ ОШИБКА: {error_msg}")
                return 1
        
        # Step 3: Generate PDF
        print(f"\n[3/3] Генерация PDF отчёта...")
        logger.info("Step 3: Generating PDF report")
        
        # Check template exists
        if not args.template.exists():
            error_msg = f"Шаблон не найден: {args.template}"
            logger.error(error_msg)
            print(f"\n✗ ОШИБКА: {error_msg}")
            return 1
        
        # CSS path
        css_path = args.template.parent / 'style.css'
        
        try:
            generate_pdf_report(
                report_data=report_data,
                output_path=args.output,
                template_path=args.template,
                css_path=css_path,
                transcript_filename=args.input.name,
                image_uri=image_uri,
                image_failed=image_failed
            )
            
            # Success summary
            print("\n" + "=" * 60)
            print("ГОТОВО!")
            print("=" * 60)
            print(f"Отчёт: {args.output.absolute()}")
            print(f"Размер: {args.output.stat().st_size / 1024:.1f} KB")
            print("=" * 60)
            
            logger.info("Report generation completed successfully")
            return 0
            
        except Exception as e:
            error_msg = f"Ошибка генерации PDF: {e}"
            logger.error(error_msg, exc_info=True)
            print(f"\n✗ ОШИБКА: {error_msg}")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n✗ Прервано пользователем")
        logger.warning("Process interrupted by user")
        return 130
    
    except Exception as e:
        error_msg = f"Неожиданная ошибка: {e}"
        logger.error(error_msg, exc_info=True)
        print(f"\n✗ КРИТИЧЕСКАЯ ОШИБКА: {error_msg}")
        print("Проверьте logs/app.log для подробной информации.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
