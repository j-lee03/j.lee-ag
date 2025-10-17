from PIL import Image, ImageDraw, ImageFont

def design_business_card(data, output_filename="my_business_card.png"):
    """
    주어진 데이터를 바탕으로 세련된 디지털 명함 이미지를 생성합니다.
    """
    # --- 1. 기본 설정 ---
    # 명함 사이즈 (가로 90mm, 세로 50mm -> 픽셀로 변환, 300DPI 기준)
    width, height = 1063, 591
    background_color = (255, 255, 255) # 흰색 배경

    # 디자인 포인트 색상
    primary_color = (25, 44, 78)    # 남색 계열
    secondary_color = (100, 100, 100) # 회색 계열

    # 이미지 생성
    image = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(image)

    # --- 2. 폰트 설정 ---
    try:
        # 이전에 다운로드한 Pretendard 폰트 파일명을 사용합니다.
        font_name_bold = ImageFont.truetype("Pretendard-Bold.otf", 60)
        font_name_regular = ImageFont.truetype("Pretendard-Regular.otf", 38)
        font_info = ImageFont.truetype("Pretendard-Regular.otf", 30)
    except IOError:
        print("폰트 파일을 찾을 수 없습니다! 'Pretendard-Bold.otf'와 'Pretendard-Regular.otf' 파일이 코드와 같은 폴더에 있는지 확인하세요.")
        return

    # --- 3. 디자인 요소 그리기 ---
    # 왼쪽 컬러 사이드바
    sidebar_width = 300
    draw.rectangle([0, 0, sidebar_width, height], fill=primary_color)

    # --- 4. 텍스트 정보 배치 ---
    # 이름과 직책
    name_x, name_y = 350, 200
    draw.text((name_x, name_y), data['name'], font=font_name_bold, fill=primary_color)
    draw.text((name_x, name_y + 80), data['title'], font=font_name_regular, fill=secondary_color)

    # 구분선
    draw.line([name_x, name_y + 140, width - 50, name_y + 140], fill=(230, 230, 230), width=2)

    # 연락처 정보 (전화, 이메일, 회사)
    info_x, info_y_start = 350, 360
    line_spacing = 50 # 줄 간격

    draw.text((info_x, info_y_start), f"P | {data['phone']}", font=font_info, fill=secondary_color)
    draw.text((info_x, info_y_start + line_spacing), f"E | {data['email']}", font=font_info, fill=secondary_color)
    draw.text((info_x, info_y_start + line_spacing * 2), f"C | {data['company']}", font=font_info, fill=secondary_color)

    # --- 5. 이미지 저장 ---
    image.save(output_filename)
    print(f"'{output_filename}' 이름으로 명함이 성공적으로 저장되었습니다!")


# --- 실행 부분 ---
if __name__ == "__main__":
    # 이 부분의 정보를 수정하여 나만의 명함을 만드세요.
    my_info = {
        "name": "j-lee",
        "title": "Software Engineer | Full-Stack Developer",
        "company": "Gemini Labs",
        "phone": "010-8039-3479",
        "email": "sdf090400@gmail.com"
    }

    design_business_card(이현직)