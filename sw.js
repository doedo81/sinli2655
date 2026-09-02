/* 아침칠판 서비스워커 — "설치(PWA)"를 켜기 위한 최소 워커.
   ⚠️ 일부러 아무것도 캐시하지 않음: 항상 네트워크에서 최신본을 받음
   (캐시하면 push 배포 후에도 옛 버전이 뜰 수 있어서, 학교 도구엔 캐시 안 하는 게 안전). */
self.addEventListener('install', function (e) { self.skipWaiting(); });
self.addEventListener('activate', function (e) { e.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', function (e) { /* 기본 네트워크 처리(캐시 안 함) */ });
