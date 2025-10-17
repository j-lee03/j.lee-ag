import io
import os
import boto3
import requests
from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# .env 파일이 있다면 로드 (로컬 테스트용)
load_dotenv()

# --- S3 및 DB 설정 (환경 변수에서 로드) ---
S3_BUCKET = os.environ.get('S3_BUCKET')
S3_KEY = os.environ.get('S3_KEY')
S3_SECRET = os.environ.get('S3_SECRET')
S3_LOCATION = f'https://{S3_BUCKET}.s3.amazonaws.com/' # http 대신 https 사용 권장

s3 = boto3.client(
    "s3",
    aws_access_key_id=S3_KEY,
    aws_secret_access_key=S3_SECRET
)

# --- Flask 앱 및 DB 설정 ---
app = Flask(__name__)
db_uri = os.environ.get('DATABASE_URL')
# Vercel에서 postgres 주소를 postgresql로 자동 변환해주는 경우가 많지만, 호환성을 위해 코드 추가
if db_uri and db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# --- S3 파일 업로드 함수 ---
def upload_file_to_s3(file, bucket_name, acl="public-read"):
    try:
        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )
    except Exception as e:
        print("S3 업로드 에러: ", e)
        return e
    return f"{S3_LOCATION}{file.filename}"


# --- 데이터베이스 모델 ---
class BusinessCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    title = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    logo_url = db.Column(db.String(255)) # 파일명이 아닌 전체 URL 저장


# --- 명함 이미지 디자인 함수 ---
def design_business_card(card_data):
    # (이전과 동일한 이미지 생성 로직)
    width, height = 1063, 591
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    font_name_bold = ImageFont.truetype("Pretendard-Bold.otf", 60)
    font_name_regular = ImageFont.truetype("Pretendard-Regular.otf", 38)
    font_info = ImageFont.truetype("Pretendard-Regular.otf", 30)

    primary_color = (25, 44, 78); secondary_color = (100, 100, 100)
    sidebar_width = 300
    draw.rectangle([0, 0, sidebar_width, height], fill=primary_color)

    if card_data.get('logo_url'):
        try:
            response = requests.get(card_data['logo_url'], stream=True)
            response.raise_for_status()
            logo_image = Image.open(io.BytesIO(response.content)).convert("RGBA")
            logo_image.thumbnail((200, 100), Image.Resampling.LANCZOS)
            logo_x = (sidebar_width - logo_image.width) // 2
            logo_y = (height - logo_image.height) // 2 - 100

            base_image_rgba = image.convert("RGBA")
            temp_layer = Image.new("RGBA", base_image_rgba.size, (255, 255, 255, 0))
            temp_layer.paste(logo_image, (logo_x, logo_y))
            image = Image.alpha_composite(base_image_rgba, temp_layer).convert("RGB")
            draw = ImageDraw.Draw(image)
        except Exception as e:
            print(f"로고 URL 처리 오류: {e}")

    name_x, name_y = 350, 200
    draw.text((name_x, name_y), card_data.get('name', ''), font=font_name_bold, fill=primary_color)
    draw.text((name_x, name_y + 80), card_data.get('title', ''), font=font_name_regular, fill=secondary_color)
    draw.line([name_x, name_y + 140, width - 50, name_y + 140], fill=(230, 230, 230), width=2)
    info_x, info_y_start = 350, 360
    line_spacing = 50
    draw.text((info_x, info_y_start), f"P | {card_data.get('phone', '')}", font=font_info, fill=secondary_color)
    draw.text((info_x, info_y_start + line_spacing), f"E | {card_data.get('email', '')}", font=font_info, fill=secondary_color)
    draw.text((info_x, info_y_start + line_spacing * 2), f"C | {card_data.get('company', '')}", font=font_info, fill=secondary_color)

    img_io = io.BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

# DB 테이블 생성 로직
with app.app_context():
    db.create_all()

# --- 라우팅 ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        logo_full_url = ""
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '':
                file.filename = secure_filename(file.filename)
                logo_full_url = upload_file_to_s3(file, S3_BUCKET)

        new_card = BusinessCard(
            name=request.form.get('name'),
            company=request.form.get('company'),
            title=request.form.get('title'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            logo_url=logo_full_url
        )
        db.session.add(new_card)
        db.session.commit()
        return redirect(url_for('index'))

    cards = BusinessCard.query.order_by(BusinessCard.id.desc()).all()
    return render_template('index.html', cards=cards)

@app.route('/card/<int:id>')
def generate_card_image(id):
    card = db.session.get(BusinessCard, id)
    card_data = {"logo_url": card.logo_url, "name": card.name, "title": card.title, "company": card.company, "phone": card.phone, "email": card.email}
    image_buffer = design_business_card(card_data)
    return send_file(image_buffer, mimetype='image/png')

@app.route('/delete/<int:id>')
def delete(id):
    card_to_delete = db.session.get(BusinessCard, id)
    # (S3 파일 삭제 로직은 복잡하므로 일단 생략)
    db.session.delete(card_to_delete)
    db.session.commit()
    return redirect(url_for('index'))