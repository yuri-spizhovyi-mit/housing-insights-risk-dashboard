import type {
  CSSProperties,
  MouseEventHandler,
  ReactNode,
  ButtonHTMLAttributes,
} from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  className?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  onClick?: () => void;
  onMouseMove?: MouseEventHandler<HTMLButtonElement>;
  onMouseEnter?: MouseEventHandler<HTMLButtonElement>;
  onMouseLeave?: MouseEventHandler<HTMLButtonElement>;
  style?: CSSProperties; // ✅ allows passing dynamic --x, --y variables safely
}

function Button({
  children,
  leftIcon,
  rightIcon,
  className = "",
  onClick,
  onMouseMove,
  onMouseEnter,
  onMouseLeave,
  style,
  ...rest
}: ButtonProps) {
  return (
    <button
      onClick={onClick}
      onMouseMove={onMouseMove}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      style={style}
      {...rest}
      className={`flex cursor-pointer items-center gap-2 ${className}`}
    >
      {leftIcon}
      {children}
      {rightIcon}
    </button>
  );
}

export default Button;
