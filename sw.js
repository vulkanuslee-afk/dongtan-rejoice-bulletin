/* 서비스워커 — 껍데기만 캐시하고, 주보 데이터는 항상 새로 받아옵니다.
   (주보가 바뀌었는데 옛 내용이 보이는 사고를 막기 위한 설계입니다) */
var SHELL = 'bulletin-shell-v2';
var SHELL_FILES = ['./', './index.html', './manifest.webmanifest',
  './assets/logo.png', './assets/hero.jpg', './assets/icon-192.png'];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(SHELL).then(function (c) { return c.addAll(SHELL_FILES); }));
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

self.addEventListener('fetch', function (e) {
  var url = new URL(e.request.url);
  var isData = url.pathname.indexOf('/data/') !== -1;

  if (isData) {
    // 주보 데이터: 네트워크 우선, 끊겼을 때만 캐시
    e.respondWith(
      fetch(e.request).then(function (res) {
        var copy = res.clone();
        caches.open(SHELL).then(function (c) { c.put(e.request, copy); });
        return res;
      }).catch(function () { return caches.match(e.request); })
    );
    return;
  }

  // 나머지: 캐시 우선
  e.respondWith(
    caches.match(e.request).then(function (hit) { return hit || fetch(e.request); })
  );
});
