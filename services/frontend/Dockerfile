# ── Раздача веб-интерфейса через Nginx (порт 8501) ─────────────────────
FROM nginx:alpine

# Копируем конфигурацию Nginx (порт 8501)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копируем статические файлы веб-интерфейса
COPY static/ /usr/share/nginx/html/

EXPOSE 8501

CMD ["nginx", "-g", "daemon off;"]
