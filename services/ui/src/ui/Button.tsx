import type { ReactNode } from "react";

interface ButtonProps {
  children: ReactNode;
  className?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  onClick?: () => void;
}

function Button({
  children,
  leftIcon,
  rightIcon,
  className = "",
  onClick,
}: ButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`flex cursor-pointer items-center gap-2 ${className}`}
    >
      {leftIcon} {children} {rightIcon}
    </button>
  );
}

export default Button;
