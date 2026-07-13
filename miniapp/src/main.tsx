import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";

import "./theme.css";
import App from "./App";
import { initTelegram } from "./telegram";

initTelegram();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {/* از MemoryRouter استفاده می‌کنیم نه HashRouter — چون تلگرام از بخش hash آدرس
        برای تزریق initData استفاده می‌کند (گاهی کمی بعد از لود اولیه) و هر روتری که به
        location.hash وابسته باشد با آن تداخل پیدا می‌کند و صفحه را خالی نشان می‌دهد. */}
    <MemoryRouter initialEntries={["/"]}>
      <App />
    </MemoryRouter>
  </StrictMode>,
);
