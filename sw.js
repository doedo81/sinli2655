/* 아침칠판 서비스워커 — "설치(PWA)"용 + 항상 최신본 보장.
   ⚠️ 아무것도 캐시하지 않고, HTML(페이지 이동) 요청은 브라우저 HTTP 캐시까지 우회해
   네트워크에서 새로 받는다(설치앱에서 옛 버전이 뜨는 문제 방지). */
self.addEventListener('install', function (e) { self.skipWaiting(); });
self.addEventListener('activate', function (e) {
  e.waitUntil((async function () {
    // 혹시 남아있는 옛 캐시 전부 삭제
    try { var keys = await caches.keys(); await Promise.all(keys.map(function (k) { return caches.delete(k); })); } catch (err) {}
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', function (e) {
  var req = e.request;
  // 페이지(HTML) 이동 요청은 캐시 우회하고 항상 최신 받기
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req, { cache: 'reload' }).catch(function () { return fetch(req); }));
  }
  /* 그 외(스크립트/이미지 등)는 기본 네트워크 처리 */
});
