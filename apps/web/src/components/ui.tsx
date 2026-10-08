import { cloneElement, isValidElement, useEffect, useId, useRef } from 'react';
import type { ButtonHTMLAttributes, HTMLAttributes, ReactElement, ReactNode } from 'react';
import { content } from '../data';

const iconPaths: Record<string, string> = {
  grid: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
  spark: 'm12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z',
  wave: 'M3 10v4 M7 6v12 M12 3v18 M17 7v10 M21 10v4',
  phone: 'M7 3H4a1 1 0 0 0-1 1c0 9.4 7.6 17 17 17a1 1 0 0 0 1-1v-3l-5-2-2 2a14 14 0 0 1-7-7l2-2Z',
  calendar:
    'M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z M7 3v4 M17 3v4 M3 10h18 M8 14h2 M14 14h2',
  users:
    'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8 M17 4a4 4 0 0 1 0 7 M22 21v-2a4 4 0 0 0-3-4',
  flow: 'M5 5h5v5H5z M14 14h5v5h-5z M10 7h7v7 M7 10v7h7',
  book: 'M12 5C9 3 5 3 2 4v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1Z M12 5v15',
  check: 'm6 12 4 4 8-8 M21 12a9 9 0 1 1-4-7.5',
  link: 'm10 13 4-4 M8 16l-2 2a4 4 0 0 1-6-6l4-4a4 4 0 0 1 6 0 M14 8l2-2a4 4 0 0 1 6 6l-4 4a4 4 0 0 1-6 0',
  chart: 'M4 3v18h17 M9 16v-5 M14 16V7 M19 16v-9',
  clock: 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0 M12 7v5l3 2',
  search: 'M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0 m-2 5 6 6',
  arrow: 'M4 12h15 m-6-6 6 6-6 6',
  chevron: 'm9 5 7 7-7 7',
  plus: 'M12 5v14 M5 12h14',
  x: 'm6 6 12 12 M18 6 6 18',
  menu: 'M4 6h16 M4 12h16 M4 18h16',
  upload: 'M12 16V3 m-5 5 5-5 5 5 M4 15v5h16v-5',
  alert: 'm12 3 10 18H2Z M12 9v5 M12 17v1',
  play: 'm8 4 12 8-12 8Z',
  pause: 'M8 4v16 M16 4v16',
  shield: 'm12 3 9 4v5c0 5-9 9-9 9S3 17 3 12V7Z m-4 9 3 3 5-6',
};
export function Icon({ name, size = 20 }: { name: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={iconPaths[name] ?? iconPaths.grid} />
    </svg>
  );
}
export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <a className="brand" href="#/welcome" aria-label={content.labels.showcase}>
      <span className="brand-mark">
        <Icon name="wave" size={24} />
      </span>
      {!compact && (
        <span>
          {content.brand}
          <small>{content.subtitle}</small>
        </span>
      )}
    </a>
  );
}
export function Button({
  children,
  variant = 'primary',
  icon,
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  icon?: string;
}) {
  return (
    <button className={`button button-${variant} ${className}`} {...props}>
      {icon && <Icon name={icon} size={17} />}
      <span>{children}</span>
    </button>
  );
}
export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: string }) {
  return (
    <span className={`badge badge-${tone}`}>
      <span className="badge-dot" />
      {children}
    </span>
  );
}
export function Empty({
  title = content.labels.noResults,
  detail = content.labels.emptyHint,
  action,
}: {
  title?: string;
  detail?: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <Icon name="search" size={26} />
      </span>
      <h3>{title}</h3>
      <p>{detail}</p>
      {action}
    </div>
  );
}
export function Notice({ children, warning = false }: { children: ReactNode; warning?: boolean }) {
  return (
    <div className={`notice ${warning ? 'notice-warning' : ''}`}>
      <Icon name={warning ? 'alert' : 'shield'} size={18} />
      <span>{children}</span>
    </div>
  );
}
export function Modal({
  title,
  children,
  onClose,
  wide = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    ref.current?.showModal();
    return () => {
      previous?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={`modal ${wide ? 'modal-wide' : ''}`}
      aria-labelledby="modal-title"
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          const r = e.currentTarget.getBoundingClientRect();
          if (
            e.clientX < r.left ||
            e.clientX > r.right ||
            e.clientY < r.top ||
            e.clientY > r.bottom
          )
            onClose();
        }
      }}
    >
      <div className="modal-header">
        <h2 id="modal-title">{title}</h2>
        <button className="icon-button" onClick={onClose} aria-label={content.labels.close}>
          <Icon name="x" />
        </button>
      </div>
      <div className="modal-body">{children}</div>
    </dialog>
  );
}
export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
}) {
  const id = useId();
  const control = isValidElement(children)
    ? cloneElement(children as ReactElement<HTMLAttributes<HTMLElement>>, {
        'aria-labelledby': id,
        ...(hint ? { 'aria-describedby': `${id}-hint` } : {}),
      })
    : children;
  return (
    <label className="field">
      <span id={id}>{label}</span>
      {control}
      {hint && <small id={`${id}-hint`}>{hint}</small>}
    </label>
  );
}
