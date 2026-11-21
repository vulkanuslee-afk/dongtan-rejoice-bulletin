/* 서비스워커
   원칙: "주보는 늘 최신이 보여야 한다"
   - 앱 화면(index.html)과 주보 내용(data/)은 항상 새것을 먼저 받아옵니다.
   - 인터넷이 끊겼을 때만 저장해 둔 것을 보여 줍니다.
   - 로고·사진처럼 안 바뀌는 것만 저장본을 먼저 씁니다. */
var SHELL = 'bulletin-shell-v5';
var SHELL_FILES = ['./', './index.html', './manifest.webmanifest',
  './assets/logo.png', './assets/hero.jpg?v=20261122', './assets/icon-192.png?v=3'];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(SHELL).then(function (c) {
    return c.addAll(SHELL_FILES.map(function (u) {
      return new Request(u, { cache: 'reload' });
    }));
  }));
  self.skipWaiting();
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== SHELL; })
        .map(function (k) { return caches.delete(k); }));
    })
  );
  self.clients.claim();
});

function networkFirst(req) {
  /* 그냥 fetch 하면 브라우저가 들고 있던 옛 파일을 그대로 줍니다.
     (주보를 올렸는데 교인 폰에 이전 화면이 뜨던 원인)
     cache:'reload' 로 매번 서버까지 다녀오게 합니다. */
  var fresh = req;
  try { fresh = new Request(req.url, { cache: 'reload', credentials: 'same-origin' }); }
  catch (e) { /* 지원 안 하면 원래 요청 그대로 */ }

  return fetch(fresh).then(function (res) {
    if (res && res.ok) {
      var copy = res.clone();
      caches.open(SHELL).then(function (c) { c.put(req, copy); });
    }
    return res;
  }).catch(function () {
    // 오프라인: ?v=... 가 달라도 저장해 둔 같은 파일을 찾아 줍니다
    return caches.match(req, { ignoreSearch: true }).then(function (hit) {
      return hit || caches.match('./index.html');
    });
  });
}

function cacheFirst(req) {
  return caches.match(req).then(function (hit) {
    return hit || fetch(req).then(function (res) {
      if (res && res.ok) {
        var copy = res.clone();
        caches.open(SHELL).then(function (c) { c.put(req, copy); });
      }
      return res;
    });
  });
}

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;

  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  var isDoc = req.mode === 'navigate' ||
              url.pathname.endsWith('/') ||
              url.pathname.endsWith('.html');
  var isData = url.pathname.indexOf('/data/') !== -1;

  e.respondWith((isDoc || isData) ? networkFirst(req) : cacheFirst(req));
});
