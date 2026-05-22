"""CLI: python resume.py"""
from builder import default_data, generate_pdf, load_data, save_data


def main():
    data = load_data()
    if not data:
        data = default_data()
        save_data(data)
    path = generate_pdf(data)
    print(f"이력서 PDF 생성 완료: {path}")


if __name__ == "__main__":
    main()
