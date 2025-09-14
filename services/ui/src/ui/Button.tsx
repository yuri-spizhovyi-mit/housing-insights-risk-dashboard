import type { ReactNode } from "react";

interface ButtonProps {
  children: ReactNode;
  className?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

function Button({
  children,
  leftIcon,
  rightIcon,
  className = "",
}: ButtonProps) {
  return (
    <button className={`flex cursor-pointer items-center gap-2 ${className}`}>
      {leftIcon} {children} {rightIcon}
    </button>
  );
}

export default Button;
