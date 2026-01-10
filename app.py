from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import random
from math import ceil

from models import db, NguoiDung, DeThi, CauHoi, DapAn, BaiLam, ChiTietBaiLam # cấu hình trong models.py

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return NguoiDung.query.get(int(id))
# ROUTE CHO LANDING PAGE
@app.route('/')
def index():
    return render_template('index.html')  # index.html = landing page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        role = request.form.get('role')

        if not full_name or not phone or not password or not password_confirm or not role:
            flash("Vui lòng nhập đầy đủ thông tin", "error")
            return redirect(url_for('register'))

        if len(phone) != 10 or not phone.isdigit():
            flash("Số điện thoại không đúng định dạng", "error")
            return redirect(url_for('register'))

        if NguoiDung.query.filter_by(so_dien_thoai=phone).first():
            flash("Số điện thoại đã tồn tại", "error")
            return redirect(url_for('register'))

        if password != password_confirm:
            flash("Mật khẩu xác nhận không khớp", "error")
            return redirect(url_for('register'))

        new_user = NguoiDung(
            ho_ten=full_name,
            so_dien_thoai=phone,
            mat_khau=password,  # tạm thời chưa hash
            vai_tro=role
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Đăng ký thành công, vui lòng đăng nhập!", "success")
        return redirect(url_for('login'))

    return render_template('/auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')

        if not phone or not password:
            flash("Vui lòng nhập đầy đủ thông tin", "error")
            return redirect(url_for('login'))

        user = NguoiDung.query.filter_by(
            so_dien_thoai=phone,
            mat_khau=password
        ).first()

        if not user:
            flash("Thông tin đăng nhập không chính xác", "error")
            return redirect(url_for('login'))

        login_user(user)
        flash("Đăng nhập thành công!", "success")

        if user.vai_tro == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))

    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# ------------------------
# ROUTE CHO DASHBOARD
# ------------------------
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if current_user.vai_tro != 'teacher':
        abort(403)

    de_this = DeThi.query.filter_by(giao_vien_id=current_user.id).all()
    return render_template('teacher/dashboard.html', de_this=de_this)

@app.route('/teacher/de-thi/tao-de-thi', methods=['GET', 'POST'])
@login_required
def tao_de_thi():
    if current_user.vai_tro != 'teacher':
        abort(403)

    if request.method == 'POST':
        tieu_de = request.form.get('tieu_de')
        thoi_gian = request.form.get('thoi_gian')
        ngay_bat_dau = request.form.get('ngay_bat_dau')
        ngay_ket_thuc = request.form.get('ngay_ket_thuc')
        khoi_hoc = request.form.get('khoi_hoc')
        mon_hoc = request.form.get('mon_hoc')
        mo_ta = request.form.get('mo_ta')
        mat_khau = request.form.get('mat_khau')

        if not all([tieu_de, thoi_gian, ngay_bat_dau, ngay_ket_thuc, khoi_hoc, mon_hoc, mat_khau]):
            flash("Vui lòng nhập đầy đủ thông tin", "error")
            return redirect(url_for('tao_de_thi'))

        # chuyển chuỗi datetime sang đối tượng Python
        ngay_bat_dau_dt = datetime.strptime(ngay_bat_dau, '%Y-%m-%d %H:%M')
        ngay_ket_thuc_dt = datetime.strptime(ngay_ket_thuc, '%Y-%m-%d %H:%M')

        de_thi = DeThi(
            tieu_de=tieu_de,
            thoi_gian=int(thoi_gian),
            ngay_bat_dau=ngay_bat_dau_dt,
            ngay_ket_thuc=ngay_ket_thuc_dt,
            khoi_hoc=khoi_hoc,
            mon_hoc=mon_hoc,
            mo_ta=mo_ta,
            mat_khau=mat_khau,
            giao_vien_id=current_user.id
        )

        db.session.add(de_thi)
        db.session.commit()

        flash("Tạo đề thi thành công", "success")
        return redirect(url_for('them_cau_hoi', de_thi_id=de_thi.id))

    return render_template('teacher/tao_de_thi.html')

@app.route('/teacher/de-thi/<int:de_thi_id>/sua', methods=['GET', 'POST'])
@login_required
def sua_de_thi(de_thi_id):
    # Chỉ teacher mới được phép sửa
    if current_user.vai_tro != 'teacher':
        abort(403)

    # Lấy đề thi từ DB
    de_thi = DeThi.query.get_or_404(de_thi_id)

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        de_thi.tieu_de = request.form.get('tieu_de')
        de_thi.khoi_hoc = int(request.form.get('khoi_hoc', 0))
        de_thi.mon_hoc = request.form.get('mon_hoc')
        de_thi.thoi_gian = int(request.form.get('thoi_gian', 60))
        de_thi.mat_khau = request.form.get('mat_khau')
        de_thi.mo_ta = request.form.get('mo_ta')

        # Chuyển định dạng ngày tháng sang datetime
        try:
            de_thi.ngay_bat_dau = datetime.strptime(request.form.get('ngay_bat_dau'), '%Y-%m-%d %H:%M')
            de_thi.ngay_ket_thuc = datetime.strptime(request.form.get('ngay_ket_thuc'), '%Y-%m-%d %H:%M')
        except Exception as e:
            flash("Ngày tháng không hợp lệ", "danger")
            return redirect(url_for('sua_de_thi', de_thi_id=de_thi.id))

        # Lưu vào DB
        db.session.commit()
        flash("Cập nhật đề thi thành công!", "success")
        return redirect(url_for('sua_de_thi', de_thi_id=de_thi.id))

    # GET: hiển thị form với dữ liệu hiện tại
    return render_template(
        'teacher/sua_de_thi.html',
        de_thi=de_thi
    )

@app.route('/teacher/de-thi/<int:de_thi_id>/xoa', methods=['POST'])
@login_required
def xoa_de_thi(de_thi_id):
    de_thi = DeThi.query.get_or_404(de_thi_id)

    if current_user.vai_tro != 'teacher':
        abort(403)

    db.session.delete(de_thi)
    db.session.commit()
    flash("Xóa đề thi thành công!", "success")
    return redirect(url_for('teacher_dashboard'))


@app.route('/teacher/de-thi/<int:de_thi_id>/them-cau-hoi', methods=['GET', 'POST'])
@login_required
def them_cau_hoi(de_thi_id):
    if current_user.vai_tro != 'teacher':
        abort(403)

    de_thi = DeThi.query.get_or_404(de_thi_id)

    if request.method == 'POST':
        noi_dung = request.form.get('noi_dung')
        loai = request.form.get('loai')
        # diem = request.form.get('diem')

        cau_hoi = CauHoi(
            noi_dung=noi_dung,
            loai=loai,
            # diem=float(diem),
            de_thi_id=de_thi.id
        )

        # Nếu trắc nghiệm → lưu đáp án đúng (A/B/C/D)
        if loai == 'trac_nghiem':
            dap_an_dung = request.form.get('dap_an_dung')
            cau_hoi.dap_an_dung = dap_an_dung

        db.session.add(cau_hoi)
        db.session.flush()  # để có cau_hoi.id

        # Lưu các đáp án
        if loai == 'trac_nghiem':
            for ky_hieu in ['A', 'B', 'C', 'D']:
                nd = request.form.get(f'dap_an_{ky_hieu}')
                if nd:
                    db.session.add(DapAn(
                        noi_dung=nd,
                        ky_hieu=ky_hieu,
                        cau_hoi_id=cau_hoi.id
                    ))

        db.session.commit()
        flash("Thêm câu hỏi thành công", "success")
        return redirect(url_for('them_cau_hoi', de_thi_id=de_thi.id))

    cau_hois = CauHoi.query.filter_by(de_thi_id=de_thi.id).all()
    return render_template(
        'teacher/them_cau_hoi.html',
        de_thi=de_thi,
        cau_hois=cau_hois
    )

@app.route('/teacher/de-thi/<int:de_thi_id>/sua-cau-hoi', methods=['GET', 'POST'])
@login_required
def sua_cau_hoi(de_thi_id):
    if current_user.vai_tro != 'teacher':
        abort(403)

    de_thi = DeThi.query.get_or_404(de_thi_id)
    cau_hois = CauHoi.query.filter_by(de_thi_id=de_thi.id).all()

    if request.method == 'POST':
        for cau_hoi in cau_hois:
            # Cập nhật nội dung câu hỏi
            noi_dung = request.form.get(f'noi_dung_{cau_hoi.id}')
            if noi_dung:
                cau_hoi.noi_dung = noi_dung

            if cau_hoi.loai == 'trac_nghiem':
                # Cập nhật đáp án đúng
                dap_an_dung = request.form.get(f'dap_an_dung_{cau_hoi.id}')
                if dap_an_dung:
                    cau_hoi.dap_an_dung = dap_an_dung

                # Cập nhật từng đáp án
                for dap_an in cau_hoi.dap_ans:
                    nd = request.form.get(f'dap_an_{dap_an.ky_hieu}_{cau_hoi.id}')
                    if nd is not None:
                        dap_an.noi_dung = nd

            # Tự luận thì chỉ cần cập nhật nội dung (đã làm ở trên)

            db.session.add(cau_hoi)  # Optional, SQLAlchemy tự detect thay đổi

        db.session.commit()
        flash("Cập nhật câu hỏi thành công!", "success")
        return redirect(url_for('sua_cau_hoi', de_thi_id=de_thi.id))

    return render_template(
        'teacher/sua_cau_hoi.html',
        de_thi=de_thi,
        cau_hois=cau_hois
    )


from flask import flash, redirect, url_for, render_template, request, abort
from datetime import datetime, timedelta

@app.route('/thi/<int:de_thi_id>', methods=['GET', 'POST'])
def vao_thi(de_thi_id):
    de_thi = DeThi.query.get_or_404(de_thi_id)
    now = datetime.now()

    # 1. Chưa đến giờ thi
    if de_thi.ngay_bat_dau and now < de_thi.ngay_bat_dau:
        return render_template(
            'student/thong_bao.html',
            icon='info',
            title='Chưa đến giờ thi',
            message=f'Đề thi sẽ mở vào lúc {de_thi.ngay_bat_dau.strftime("%d/%m/%Y %H:%M")}'
        )

    # 2. Đã hết hạn
    if de_thi.ngay_ket_thuc and now > de_thi.ngay_ket_thuc:
        return render_template(
            'student/thong_bao.html',
            icon='error',
            title='Đã hết thời gian thi',
            message='Đề thi này đã đóng. Bạn không thể làm bài.'
        )

    if request.method == 'POST':
        ho_ten = request.form.get('ho_ten')
        lop = request.form.get('lop')
        mat_khau = request.form.get('mat_khau')

        # Mật khẩu sai
        if mat_khau != de_thi.mat_khau:
            flash("Mật khẩu bài thi không đúng", "error")
            return redirect(request.url)

        # TẠO BÀI LÀM CHỈ KHI ĐANG TRONG THỜI GIAN
        bai_lam = BaiLam(
            de_thi_id=de_thi.id,
            ho_ten=ho_ten,
            lop=lop,
            thoi_diem_bat_dau=None  # sẽ set trong /lam-bai
        )
        db.session.add(bai_lam)
        db.session.commit()

        return redirect(url_for('lam_bai', bai_lam_id=bai_lam.id))

    return render_template('student/nhap_thong_tin.html', de_thi=de_thi)


@app.route('/lam-bai/<int:bai_lam_id>', methods=['GET'])
def lam_bai(bai_lam_id):
    bai_lam = BaiLam.query.get_or_404(bai_lam_id)
    de_thi = DeThi.query.get_or_404(bai_lam.de_thi_id)
    now = datetime.now()

    # 1. Chưa đến giờ thi
    if de_thi.ngay_bat_dau and now < de_thi.ngay_bat_dau:
        return render_template(
            'student/thong_bao.html',
            icon='info',
            title='Chưa đến giờ thi',
            message=f'Đề thi sẽ mở vào lúc {de_thi.ngay_bat_dau.strftime("%d/%m/%Y %H:%M")}'
        )

    # 2. Đã hết hạn
    if de_thi.ngay_ket_thuc and now > de_thi.ngay_ket_thuc:
        return render_template(
            'student/thong_bao.html',
            icon='error',
            title='Đã hết thời gian thi',
            message='Đề thi này đã đóng. Bạn không thể làm bài.'
        )

    # 3. Bài đã nộp
    if bai_lam.thoi_diem_nop:
        return render_template(
            'student/thong_bao.html',
            icon='warning',
            title='Bài thi đã nộp',
            message='Bạn đã nộp bài này và không thể làm lại.'
        )

    # 4. Set thời điểm bắt đầu bài làm 1 lần
    if not bai_lam.thoi_diem_bat_dau:
        bai_lam.thoi_diem_bat_dau = now
        db.session.commit()

    # 5. Tính thời gian kết thúc
    ket_thuc = bai_lam.thoi_diem_bat_dau + timedelta(minutes=de_thi.thoi_gian)

    # 6. Hết giờ nhưng chưa nộp (F5 / mở tab mới)
    if now >= ket_thuc:
        return render_template(
            'student/thong_bao.html',
            icon='error',
            title='Hết giờ làm bài',
            message='Thời gian làm bài đã kết thúc. Bài thi đã bị khóa.'
        )

    # 7. Random câu hỏi
    cau_hois = CauHoi.query.filter_by(de_thi_id=de_thi.id).all()
    random.shuffle(cau_hois)

    return render_template(
        'student/lam_bai.html',
        de_thi=de_thi,
        cau_hois=cau_hois,
        bai_lam=bai_lam,
        end_time=int(ket_thuc.timestamp()),
        now_utc=int(now.timestamp())
    )



# Route nộp bài
@app.route('/nop-bai/<int:bai_lam_id>', methods=['POST'])
def nop_bai(bai_lam_id):
    bai_lam = BaiLam.query.get_or_404(bai_lam_id)
    de_thi = DeThi.query.get_or_404(bai_lam.de_thi_id)
    cau_hois = CauHoi.query.filter_by(de_thi_id=de_thi.id).all()

    tong_diem = 0
    tong_diem_co_diem = sum(1 for ch in cau_hois if ch.loai == 'trac_nghiem') or 1

    for ch in cau_hois:
        value = request.form.get(f'q{ch.id}')  # Lấy theo id câu hỏi
        chi_tiet = ChiTietBaiLam(bai_lam_id=bai_lam.id, cau_hoi_id=ch.id)

        if ch.loai == 'trac_nghiem':
            dap_an_chon = DapAn.query.filter_by(cau_hoi_id=ch.id, ky_hieu=value).first()
            chi_tiet.dap_an_id = dap_an_chon.id if dap_an_chon else None

            # Chấm điểm
            if dap_an_chon and dap_an_chon.ky_hieu == ch.dap_an_dung:
                chi_tiet.diem = 1  # tính 1 điểm mỗi câu đúng
                tong_diem += 1
            else:
                chi_tiet.diem = 0
        else:  # tự luận, tạm lưu đáp án, điểm để giáo viên chấm
            chi_tiet.tra_loi_text = value
            chi_tiet.diem = 0

        db.session.add(chi_tiet)

    # Quy đổi thang điểm 10
    tong_diem_10 = round(tong_diem / tong_diem_co_diem * 10, 2)

    bai_lam.thoi_diem_nop = datetime.utcnow()
    bai_lam.tong_diem = tong_diem_10
    db.session.commit()

    return {"success": True, "tong_diem": tong_diem_10}

@app.route('/teacher/de-thi/<int:de_thi_id>/danh-sach-thi-sinh')
@login_required
def danh_sach_thi_sinh(de_thi_id):
    if current_user.vai_tro != 'teacher':
        abort(403)

    # Lấy đề thi và kiểm tra quyền của giáo viên
    de_thi = DeThi.query.get_or_404(de_thi_id)

    if de_thi.giao_vien_id != current_user.id:
        abort(403)  # Không phải chủ đề, không được xem

    # Lấy danh sách bài làm của thí sinh
    bai_lam_list = BaiLam.query.filter_by(de_thi_id=de_thi.id).all()

    return render_template(
        'teacher/danh_sach_thi_sinh.html',
        de_thi=de_thi,
        bai_lam_list=bai_lam_list
    )

def cham_trac_nghiem(bai_lam_id):
    chi_tiets = ChiTietBaiLam.query.filter_by(bai_lam_id=bai_lam_id).all()
    tong_diem = 0

    # Lấy danh sách câu trắc nghiệm
    cau_hois = [ct.cau_hoi for ct in chi_tiets if ct.cau_hoi.loai == 'trac_nghiem']
    if not cau_hois:
        return 0

    diem_mot_cau = 10 / len(cau_hois)

    for ct in chi_tiets:
        cau_hoi = ct.cau_hoi
        if cau_hoi.loai == 'trac_nghiem':
            dap_an_chon = DapAn.query.get(ct.dap_an_id)
            if dap_an_chon and dap_an_chon.ky_hieu == cau_hoi.dap_an_dung:
                ct.diem = diem_mot_cau
                tong_diem += diem_mot_cau
            else:
                ct.diem = 0

    db.session.commit()
    return round(tong_diem, 2)

@app.template_filter('dinh_dang_mon_hoc')
def dinh_dang_mon_hoc(value):
    mapping = {
        "tin_hoc": "Tin học",
        "am_nhac": "Âm nhạc",
        "my_thuat": "Mỹ thuật",
        "tieng_anh": "Tiếng anh",
        "cong_nghe": "Công nghệ",
        "gdkt_va_phap_luat": "Giáo dục kinh tế và Pháp luật",
        "gdqp_va_an_ninh": "Giáo dục Quốc phòng và an ninh",
        "gd_the_chat": "Giáo dục thể chất",
        "hoa_hoc": "Hóa học",
        "lich_su": "Lịch sử",
        "dia_ly": "Địa lý",
        "ngu_van": "Ngữ văn",
        "sinh_hoc": "Sinh học",
        "toan": "Toán",
        "vat_ly": "Vật lý",
        "gd_cong_dan": "Giáo dục công dân",
        "khac": "Khác",
    }
    return mapping.get(value, value)
# CHẠY APP
if __name__ == "__main__":
    import os
    # tạo folder instance nếu chưa có
    if not os.path.exists('instance'):
        os.makedirs('instance')

    with app.app_context():
        db.create_all()  # tạo bảng từ models.py
    app.run(host="127.0.0.1", port=5000, debug=True)

