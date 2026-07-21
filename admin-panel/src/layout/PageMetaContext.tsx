import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

interface PageMeta {
  title: string;
  subtitle?: string;
}

interface PageMetaContextValue {
  meta: PageMeta;
  setMeta: (meta: PageMeta) => void;
}

const PageMetaContext = createContext<PageMetaContextValue | null>(null);

export function PageMetaProvider({ children }: { children: ReactNode }) {
  const [meta, setMeta] = useState<PageMeta>({ title: "پنل مدیریت" });
  return (
    <PageMetaContext.Provider value={{ meta, setMeta }}>{children}</PageMetaContext.Provider>
  );
}

export function usePageMeta(title: string, subtitle?: string) {
  const ctx = useContext(PageMetaContext);
  if (!ctx) throw new Error("usePageMeta باید داخل PageMetaProvider استفاده شود");
  useEffect(() => {
    ctx.setMeta({ title, subtitle });
  }, [title, subtitle]);
}

export function useCurrentPageMeta() {
  const ctx = useContext(PageMetaContext);
  if (!ctx) throw new Error("useCurrentPageMeta باید داخل PageMetaProvider استفاده شود");
  return ctx.meta;
}
