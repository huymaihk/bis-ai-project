import React, { useState } from 'react';
import { DepartmentId } from '../types/bisTypes';
import { AgentRobotAvatar } from './AgentRobotAvatar';
import {
  Lock,
  UserCheck,
  Eye,
  EyeOff,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  Sparkles,
  Building2,
} from 'lucide-react';

export interface AuthenticatedStaffUser {
  fullName: string;
  email: string;
  roleLabel: string;
  department: DepartmentId;
}

interface LoginViewProps {
  onLoginSuccess: (user: AuthenticatedStaffUser) => void;
}

const DEMO_STAFF_ACCOUNTS: {
  id: string;
  fullName: string;
  email: string;
  passwordHint: string;
  roleLabel: string;
  department: DepartmentId;
}[] = [
  {
    id: 'staff-minhanh',
    fullName: 'Nguyễn Minh Anh',
    email: 'minhanh.nguyen@bistextile.vn',
    passwordHint: 'BIS@03026A',
    roleLabel: 'Điều hành viên · BIS Textile',
    department: 'overview',
  },
  {
    id: 'staff-huymai',
    fullName: 'Huy Mai',
    email: 'huymai0156@gmail.com',
    passwordHint: 'BIS@2026PRO',
    roleLabel: 'Kỹ sư Trưởng · BIS_AI_PROJECT',
    department: 'overview',
  },
];

const ROBOT_GREETINGS: {
  id: DepartmentId;
  name: string;
  role: string;
  greeting: string;
}[] = [
  {
    id: 'overview',
    name: 'Chỉ huy BIS',
    role: 'Bàn họp 03026A',
    greeting:
      'Chỉ huy BIS: Chào mừng bạn! Toàn bộ 7 Robot đã sẵn sàng đi lại, chạy nhảy và báo cáo trực tiếp phiên 03026A!',
  },
  {
    id: 'technical',
    name: 'Technical Robot',
    role: 'Spec · PDF Trang 16',
    greeting:
      'Technical Robot: Đã bóc tách thông số máy đo độ bền kéo vải 03026A (0.5 – 50 kN, ±0.5%) từ trang 16 PDF!',
  },
  {
    id: 'marketing',
    name: 'Marketing Robot',
    role: 'Biên tập VI/EN · SEO',
    greeting:
      'Marketing Robot: Đã chuẩn bị mô tả song ngữ VI/EN và tối ưu SEO 148/160 ký tự đạt chuẩn xanh!',
  },
  {
    id: 'imagestudio',
    name: 'Image Studio Robot',
    role: 'Buồng chụp Benchmark',
    greeting:
      'Image Studio Robot: Đang xử lý 7 ảnh sản phẩm 03026A trong buồng chụp BIS, chờ bạn vào phê duyệt!',
  },
  {
    id: 'operations',
    name: 'Operations Robot',
    role: 'Kiểm trùng · Haravan',
    greeting:
      'Operations Robot: Đã đối soát mã tương tự 03026 (92%) và sẵn sàng tạo bản nháp trên Haravan!',
  },
  {
    id: 'knowledge',
    name: 'Knowledge Robot',
    role: 'Thư viện ISO 13934-1',
    greeting:
      'Knowledge Robot: Đã lập chỉ mục 68 tài liệu tiêu chuẩn quốc tế ISO 13934-1 và ASTM D5034!',
  },
];

export const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess }) => {
  const [emailInput, setEmailInput] = useState<string>('minhanh.nguyen@bistextile.vn');
  const [passwordInput, setPasswordInput] = useState<string>('BIS@03026A');
  const [selectedDept, setSelectedDept] = useState<DepartmentId>('overview');
  const [rememberSession, setRememberSession] = useState<boolean>(true);
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [activeRobotIdx, setActiveRobotIdx] = useState<number>(0);

  const handleSelectPresetAccount = (acc: (typeof DEMO_STAFF_ACCOUNTS)[0]) => {
    setEmailInput(acc.email);
    setPasswordInput(acc.passwordHint);
    setSelectedDept(acc.department);
    setErrorMessage('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedEmail = emailInput.trim();
    const trimmedPass = passwordInput.trim();

    if (!trimmedEmail || !trimmedPass) {
      setErrorMessage(
        'Vui lòng nhập đầy đủ Email/Mã nhân sự và Mật khẩu nội bộ được cấp phát.'
      );
      return;
    }

    if (trimmedPass.length < 4) {
      setErrorMessage('Mật khẩu nội bộ không hợp lệ. Vui lòng kiểm tra lại.');
      return;
    }

    const matchedPreset = DEMO_STAFF_ACCOUNTS.find(
      (a) => a.email.toLowerCase() === trimmedEmail.toLowerCase()
    );

    onLoginSuccess({
      fullName: matchedPreset ? matchedPreset.fullName : 'Nguyễn Minh Anh',
      email: trimmedEmail,
      roleLabel: matchedPreset ? matchedPreset.roleLabel : 'Điều hành viên · BIS Textile',
      department: selectedDept,
    });
  };

  const currentGreeting = ROBOT_GREETINGS[activeRobotIdx] || ROBOT_GREETINGS[0];

  return (
    <div className="min-h-screen bg-[#161210] text-[#FAF6F0] flex flex-col justify-between p-4 lg:p-6">
      {/* Top Bar */}
      <header className="max-w-[1440px] w-full mx-auto flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#332924]">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-black italic tracking-tighter text-[#E03B2F]">
            BIS
          </span>
          <span className="text-sm font-extrabold tracking-wider text-[#FAF6F0]">
            TEXTILE AI · Phòng điều hành
          </span>
          <span className="text-[#6E5A4F]" aria-hidden="true">|</span>
          <span className="text-xs font-mono text-[#D5C7BC]">
            G:\My Drive\BIS_AI_PROJECT
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs text-[#D5C7BC]">
          <ShieldCheck className="w-4 h-4 text-[#10B981]" />
          <span>Cổng xác thực nhân sự nội bộ (Không tự đăng ký)</span>
          <span aria-hidden="true">·</span>
          <span className="font-mono text-[#F59E0B]">Phiên 03026A</span>
        </div>
      </header>

      {/* Main 12-Col Grid: Left 7 Cols (3D Room & Porcelain Robots Showcase) + Right 5 Cols (Enterprise Login Form) */}
      <main className="max-w-[1440px] w-full mx-auto my-auto py-4 grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* LEFT 7 COLS: 3D BIS Command Room & Porcelain Robots Welcome Showcase */}
        <div className="lg:col-span-7 rounded-2xl overflow-hidden border border-[#5A463C] frame-8d-stage flex flex-col justify-between">
          {/* Cropped 3D Command Room Scene matching image_2c606f3c.png */}
          <div className="relative w-full aspect-[16/11] min-h-[340px] overflow-hidden select-none">
            <img
              src="/assets/aistudio/image_bff76a11.png"
              alt="Phòng điều hành 3D BIS TEXTILE AI với đội ngũ Robot"
              className="absolute max-w-none pointer-events-none"
              style={{
                left: '-20.6%',
                top: '-9.9%',
                width: '165%',
                height: '130%',
              }}
            />

            {/* Top Live Robot Welcome Speech Banner */}
            <div className="relative z-10 p-4">
              <div className="bg-gradient-to-b from-[#2A1F1A]/95 to-[#18120F]/95 border border-[#8A6B58] rounded-2xl px-4 py-2.5 text-xs text-[#FAF6F0] flex items-center gap-3 shadow-[inset_0_1px_0_rgba(255,248,235,0.18),0_10px_24px_-4px_rgba(0,0,0,0.68)]">
                <span className="w-2.5 h-2.5 rounded-full bg-[#E03B2F] shrink-0" />
                <span className="font-semibold leading-relaxed">
                  {currentGreeting.greeting}
                </span>
              </div>
            </div>
          </div>

          {/* Interactive Porcelain Robot Roster Strip at Bottom of Showcase */}
          <div className="p-4 card-8d-dark border-t border-[#4E3E36] space-y-2.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-[#FAF6F0] flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#F59E0B]" />
                <span>Đội ngũ Robot Tác tử 3D đang trực phiên 03026A (Bấm để nghe báo cáo):</span>
              </span>
              <span className="font-mono text-[11px] text-[#B8AAA0]">
                6 Trạm chuyên trách
              </span>
            </div>

            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
              {ROBOT_GREETINGS.map((rob, idx) => {
                const isSelected = activeRobotIdx === idx;
                return (
                  <button
                    key={rob.id}
                    type="button"
                    onClick={() => setActiveRobotIdx(idx)}
                    className={`p-2 rounded-xl border text-center transition-all flex flex-col items-center gap-1 cursor-pointer ${
                      isSelected
                        ? 'bg-gradient-to-b from-[#3A2822] to-[#261A16] border-[#E03B2F] shadow-[inset_0_1px_0_rgba(255,248,235,0.16),0_6px_14px_rgba(0,0,0,0.5)]'
                        : 'card-8d-dark-recessed border-[#433630] hover:border-[#8C6D5B]'
                    }`}
                  >
                    <AgentRobotAvatar
                      department={rob.id}
                      size="sm"
                      isActive={isSelected}
                    />
                    <div className="text-[11px] font-bold text-[#FAF6F0] truncate w-full">
                      {rob.name.replace(' Robot', '')}
                    </div>
                    <div className="text-[9px] text-[#B8AAA0] truncate w-full">
                      {rob.role}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* RIGHT 5 COLS: Warm Ivory & Espresso Enterprise Login Card (NO Sign-Up / Registration) */}
        <div className="lg:col-span-5 card-8d-ivory text-[#1E1916] border border-[#D8CEC2] rounded-2xl p-6 lg:p-7 flex flex-col justify-between">
          <div className="space-y-5">
            {/* Card Header */}
            <div className="flex items-start justify-between gap-3 border-b border-[#E2D8CC] pb-4">
              <div>
                <div className="text-xs font-extrabold uppercase tracking-wider text-[#B91C1C] flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5" />
                  <span>Hệ thống Quản trị Sản phẩm Dệt may</span>
                </div>
                <h1 className="text-xl lg:text-2xl font-black text-[#1E1916] mt-1">
                  Đăng nhập Phòng điều hành
                </h1>
                <p className="text-xs text-[#574B43] mt-0.5">
                  Truy cập không gian làm việc 3D đa tác tử và 6 phân hệ nghiệp vụ chuẩn BIS.
                </p>
              </div>
              <AgentRobotAvatar department="overview" size="sm" isActive />
            </div>

            {/* Quick Staff Role Selection Presets */}
            <div className="space-y-1.5">
              <div className="text-xs font-bold text-[#473C35]">
                Chọn nhanh tài khoản nhân sự đang được cấp quyền:
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {DEMO_STAFF_ACCOUNTS.map((acc) => {
                  const isCurrent = emailInput.toLowerCase() === acc.email.toLowerCase();
                  return (
                    <button
                      key={acc.id}
                      type="button"
                      onClick={() => handleSelectPresetAccount(acc)}
                      className={`p-2.5 rounded-xl border text-left transition-all flex items-center gap-2.5 cursor-pointer ${
                        isCurrent
                          ? 'bg-gradient-to-b from-[#FFF7F5] to-[#FCE8E4] border-[#D9382C] shadow-[inset_0_1px_0_#FFFFFF,0_4px_10px_rgba(217,56,44,0.16)]'
                          : 'card-8d-interactive border-[#DED4C8]'
                      }`}
                    >
                      <div className="w-8 h-8 rounded-full bg-gradient-to-b from-[#46352D] to-[#2B201B] text-[#FAF6F0] flex items-center justify-center shrink-0 shadow-sm">
                        <UserCheck className="w-4 h-4 text-[#E03B2F]" />
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs font-extrabold text-[#1E1916] truncate">
                          {acc.fullName}
                        </div>
                        <div className="text-[10px] text-[#6E5D53] truncate">
                          {acc.roleLabel}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Login Form (Strictly NO Sign-Up / Registration) */}
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              <div>
                <label
                  htmlFor="bis-login-email"
                  className="block text-xs font-bold text-[#3B302B] mb-1"
                >
                  Email nội bộ hoặc Mã nhân sự <span className="text-[#D9382C]">*</span>
                </label>
                <input
                  id="bis-login-email"
                  type="text"
                  value={emailInput}
                  onChange={(e) => {
                    setEmailInput(e.target.value);
                    if (errorMessage) setErrorMessage('');
                  }}
                  placeholder="vd: minhanh.nguyen@bistextile.vn"
                  className="w-full bg-white text-[#1E1916] text-sm font-medium px-3.5 py-2.5 rounded-xl border border-[#C9BBAE] shadow-inner focus:outline-none focus:border-[#D9382C]"
                />
              </div>

              <div>
                <label
                  htmlFor="bis-login-password"
                  className="block text-xs font-bold text-[#3B302B] mb-1"
                >
                  Mật khẩu nội bộ <span className="text-[#D9382C]">*</span>
                </label>
                <div className="relative">
                  <input
                    id="bis-login-password"
                    type={showPassword ? 'text' : 'password'}
                    value={passwordInput}
                    onChange={(e) => {
                      setPasswordInput(e.target.value);
                      if (errorMessage) setErrorMessage('');
                    }}
                    placeholder="Nhập mật khẩu được IT cấp..."
                    className="w-full bg-white text-[#1E1916] text-sm font-mono px-3.5 py-2.5 pr-10 rounded-xl border border-[#C9BBAE] shadow-inner focus:outline-none focus:border-[#D9382C]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-[#6E5D53] hover:text-[#1E1916]"
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              <div>
                <label
                  htmlFor="bis-login-dept"
                  className="block text-xs font-bold text-[#3B302B] mb-1"
                >
                  Khu vực làm việc mở đầu sau khi đăng nhập
                </label>
                <select
                  id="bis-login-dept"
                  value={selectedDept}
                  onChange={(e) => setSelectedDept(e.target.value as DepartmentId)}
                  className="w-full bg-white text-[#1E1916] text-xs font-bold px-3.5 py-2.5 rounded-xl border border-[#C9BBAE] shadow-xs focus:outline-none focus:border-[#D9382C]"
                >
                  <option value="overview">
                    Phòng điều hành 3D (Tổng quan · Bàn họp 03026A)
                  </option>
                  <option value="technical">Kỹ thuật (Technical · Trích xuất PDF)</option>
                  <option value="marketing">Marketing (Biên tập VI/EN &amp; SEO)</option>
                  <option value="imagestudio">Image Studio (Xử lý &amp; Duyệt ảnh)</option>
                  <option value="operations">Vận hành (Operations · Tạo nháp Haravan)</option>
                  <option value="knowledge">Tri thức (Knowledge · Thư viện ISO)</option>
                  <option value="memory">Bộ nhớ (Memory · Phiên bản &amp; Đồng bộ)</option>
                </select>
              </div>

              <div className="flex items-center justify-between text-xs">
                <label className="inline-flex items-center gap-2 cursor-pointer text-[#473C35] font-medium">
                  <input
                    type="checkbox"
                    checked={rememberSession}
                    onChange={(e) => setRememberSession(e.target.checked)}
                    className="rounded border-[#C9BBAE] text-[#D9382C]"
                  />
                  <span>Duy trì phiên làm việc 03026A</span>
                </label>
                <span className="font-mono text-[11px] text-[#6E5D53]">
                  Bảo mật nội bộ BIS
                </span>
              </div>

              {errorMessage && (
                <div
                  role="alert"
                  className="p-3 rounded-xl bg-[#FEE2E2] border border-[#FCA5A5] text-[#991B1B] text-xs font-semibold flex items-center gap-2"
                >
                  <AlertCircle className="w-4 h-4 shrink-0 text-[#DC2626]" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <button
                type="submit"
                data-start="true"
                className="w-full py-3 px-5 rounded-xl btn-8d-crimson text-white text-sm font-extrabold flex items-center justify-center gap-2 transition-all cursor-pointer"
              >
                <Lock className="w-4 h-4" />
                <span>Đăng nhập vào Phòng điều hành 3D</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          </div>

          {/* Internal Policy Notice: Strictly No Registration / No Password Sign-Up */}
          <div className="mt-5 pt-3.5 border-t border-[#E2D8CC] flex items-center justify-between gap-2 text-[11px] text-[#574B43]">
            <div>
              <strong>Chính sách truy cập:</strong> Tài khoản do Quản trị viên BIS TEXTILE cấp phát (Không có mục tự đăng ký tài khoản/mật khẩu).
            </div>
            {/* colorful fabric roll dots */}
            <div className="flex items-center gap-1 shrink-0">
              <span className="w-3 h-3 rounded-full bg-[#B91C1C]" />
              <span className="w-3 h-3 rounded-full bg-[#D97706]" />
              <span className="w-3 h-3 rounded-full bg-[#475569]" />
            </div>
          </div>
        </div>
      </main>

      {/* Bottom Footer */}
      <footer className="max-w-[1440px] w-full mx-auto pt-3 border-t border-[#332924] flex flex-wrap items-center justify-between gap-2 text-xs text-[#9C8D84]">
        <div>
          BIS TEXTILE AI · Hệ thống Quản lý Thiết bị, Vật tư &amp; Tiêu chuẩn Dệt may
        </div>
        <div className="font-mono">
          Phiên bản mẫu tương tác · Dữ liệu minh họa SKU 03026A
        </div>
      </footer>
    </div>
  );
};
