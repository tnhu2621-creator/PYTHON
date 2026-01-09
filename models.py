from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class NguoiDung(db.Model, UserMixin):
    __tablename__ = 'nguoi_dung'

    id = db.Column(db.Integer, primary_key=True)
    ho_ten = db.Column(db.String(150), nullable=False)
    so_dien_thoai = db.Column(db.String(10), unique=True, nullable=False)
    mat_khau = db.Column(db.String(200), nullable=False)
    vai_tro = db.Column(db.String(20), nullable=False)
    # teacher | student

class DeThi(db.Model):
    __tablename__ = 'de_thi'

    id = db.Column(db.Integer, primary_key=True)

    tieu_de = db.Column(db.String(255), nullable=False)
    mo_ta = db.Column(db.Text)

    thoi_gian = db.Column(db.Integer, nullable=False)  # phút

    ngay_bat_dau = db.Column(db.DateTime, nullable=False)
    ngay_ket_thuc = db.Column(db.DateTime, nullable=False)

    khoi_hoc = db.Column(db.String(10), nullable=False)
    mon_hoc = db.Column(db.String(50), nullable=False)

    # 🔑 quan trọng
    mat_khau = db.Column(db.String(50), nullable=False)

    giao_vien_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'))

class CauHoi(db.Model):
    __tablename__ = 'cau_hoi'

    id = db.Column(db.Integer, primary_key=True)
    noi_dung = db.Column(db.Text, nullable=False)
    loai = db.Column(db.String(20), nullable=False)
    de_thi_id = db.Column(db.Integer, db.ForeignKey('de_thi.id'))
    dap_an_dung = db.Column(db.String(1))  # A/B/C/D

    # 🔥 QUAN TRỌNG NHẤT
    dap_ans = db.relationship(
        'DapAn',
        backref='cau_hoi',
        lazy=True,
        cascade='all, delete-orphan'
    )



# chỉ dùng cho trắc nghiệm
class DapAn(db.Model):
    __tablename__ = 'dap_an'

    id = db.Column(db.Integer, primary_key=True)
    noi_dung = db.Column(db.Text, nullable=False)
    ky_hieu = db.Column(db.String(1))

    cau_hoi_id = db.Column(
        db.Integer,
        db.ForeignKey('cau_hoi.id'),
        nullable=False
    )


class BaiLam(db.Model):
    __tablename__ = 'bai_lam'

    id = db.Column(db.Integer, primary_key=True)
    de_thi_id = db.Column(db.Integer, db.ForeignKey('de_thi.id'))

    ho_ten = db.Column(db.String(100))
    lop = db.Column(db.String(50))

    thoi_diem_bat_dau = db.Column(db.DateTime, nullable=True)
    thoi_diem_nop = db.Column(db.DateTime, nullable=True)
    
    # Mới: tổng điểm thí sinh
    tong_diem = db.Column(db.Float, nullable=True)


class ChiTietBaiLam(db.Model):
    __tablename__ = 'chi_tiet_bai_lam'

    id = db.Column(db.Integer, primary_key=True)
    bai_lam_id = db.Column(db.Integer, db.ForeignKey('bai_lam.id'), nullable=False)
    cau_hoi_id = db.Column(db.Integer, db.ForeignKey('cau_hoi.id'), nullable=False)

    # Cho trắc nghiệm
    dap_an_id = db.Column(db.Integer, db.ForeignKey('dap_an.id'), nullable=True)

    # Cho tự luận
    tra_loi_text = db.Column(db.Text, nullable=True)
    file_dinh_kem = db.Column(db.String(255), nullable=True)
    diem = db.Column(db.Float, nullable=True)
