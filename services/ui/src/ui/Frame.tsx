import type { ReactNode } from "react";

interface FrameProps {
  children: ReactNode;
  className: string;
}

function Frame({ children, className }: FrameProps) {
  return (
    <div
      className={`data-frame opacity-0 rounded-2xl border text-amber-50 border-neutral-800 bg-neutral-900 p-4 ${className}`}
    >
      {children}
    </div>
  );
}

interface HeaderProps {
  leftIcon?: ReactNode;
  title: string;
  details?: string;
}

function Header({ leftIcon, title, details }: HeaderProps) {
  return (
    <div className="flex items-center justify-between mb-9 flex-wrap gap-2">
      <h2 className="font-semibold flex items-center gap-2">
        {leftIcon} {title}
      </h2>
      {details && <span className="text-xs opacity-60">{details}</span>}
    </div>
  );
}

interface BodyProps {
  children: ReactNode;
  className?: string;
}

function Body({ children, className }: BodyProps) {
  return <div className={`${className}`}>{children}</div>;
}

interface FooterProps {
  children: ReactNode;
  className: string;
}

function Footer({ children, className }: FooterProps) {
  return <div className={`${className}`}>{children}</div>;
}

Frame.Header = Header;
Frame.Body = Body;
Frame.Footer = Footer;

export default Frame;
