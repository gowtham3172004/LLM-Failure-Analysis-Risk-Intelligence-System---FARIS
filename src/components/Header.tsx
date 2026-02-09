import { Link, useLocation } from "react-router-dom";
import { cn } from "@/utils";

const navItems = [
  { path: "/", label: "Home" },
  { path: "/analyze", label: "Analyze" },
  { path: "/taxonomy", label: "Taxonomy" },
  { path: "/history", label: "History" },
  { path: "/about", label: "About" },
];

export default function Header() {
  const location = useLocation();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground font-mono font-bold text-sm">
            F
          </div>
          <span className="font-semibold text-lg tracking-tight">FARIS</span>
        </Link>

        <nav className="flex items-center gap-1">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "px-3 py-2 text-sm font-medium rounded-md transition-colors",
                location.pathname === item.path
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
