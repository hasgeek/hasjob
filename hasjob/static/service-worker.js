importScripts('https://unpkg.com/workbox-sw@2.1.2/build/importScripts/workbox-sw.prod.v2.1.2.js');

const workboxSW = new self.WorkboxSW({
  "cacheId": "hasjob",
  "skipWaiting": true,
  "clientsClaim": true
});

workboxSW.precache([
  {
    "url": "/static/build/css/stylesheet-app-css.efe6f4e46bdea6a78c39.css",
    "revision": "4a2260052465a808c72847def94ad2a9"
  },
  {
    "url": "/static/build/js/app.efe6f4e46bdea6a78c39.js",
    "revision": "9fe47feb0657e65d9c3b43b59bb648ae"
  },
  {
    "url": "/static/build/js/manifest.efe6f4e46bdea6a78c39.js",
    "revision": "fe684bf23b9518850a7a3dd90492001d"
  },
  {
    "url": "/static/build/js/vendor.efe6f4e46bdea6a78c39.js",
    "revision": "12a1ca8d2cb2caab35d21438cb595e94"
  }
]);

workboxSW.router.registerRoute(/^https?\:\/\/static.*/, workboxSW.strategies.networkFirst({
  "cacheName": "assets"
}), 'GET');

//For development setup caching of assets
workboxSW.router.registerRoute(/^http:\/\/localhost:5000\/static/, workboxSW.strategies.networkFirst({
  "cacheName": "baseframe-local"
}), 'GET');

workboxSW.router.registerRoute(/^https?\:\/\/ajax.googleapis.com\/*/, workboxSW.strategies.networkFirst({
  "cacheName": "cdn-libraries"
}), 'GET');

workboxSW.router.registerRoute(/^https?:\/\/cdnjs.cloudflare.com\/*/, workboxSW.strategies.networkFirst({
  "cacheName": "cdn-libraries"
}), 'GET');

workboxSW.router.registerRoute(/^https?:\/\/images\.hasgeek\.com\/embed\/file\/*/, workboxSW.strategies.networkFirst({
  "cacheName": "images"
}), 'GET');

workboxSW.router.registerRoute(/^https?:\/\/hasgeek.com\/*/, workboxSW.strategies.networkFirst({
  "cacheName": "images"
}), 'GET');

workboxSW.router.registerRoute(/^https?:\/\/hasjob.co\/*/, workboxSW.strategies.networkFirst({
  "cacheName": "images"
}), 'GET');

workboxSW.router.registerRoute(/^https?:\/\/fonts.googleapis.com\/*/, workboxSW.strategies.networkFirst({
  "cacheName": "fonts"
}), 'GET');

workboxSW.router.registerRoute(/^https?:\/\/fonts.gstatic.com\/*/, workboxSW.strategies.networkFirst({
  "cacheName": "fonts"
}), 'GET');

/* The service worker handles all fetch requests. If fetching of job post page or 
other pages fails due to a network error, it will return the cached "offline" page.
*/
workboxSW.router.registerRoute('/(.*)', args => {
  return workboxSW.strategies.networkFirst({cacheName: 'routes'}).handle(args).then(response => {
    if (!response) {
      return caches.match('/offline');
    } 
    return response;
  });
});

// https://googlechrome.github.io/samples/service-worker/custom-offline-page/
function createCacheBustedRequest(url) {
  let request = new Request(url, {cache: 'reload'});
  // See https://fetch.spec.whatwg.org/#concept-request-mode
  /* This is not yet supported in Chrome as of M48, so we need to 
  explicitly check to see if the cache: 'reload' option had any effect.*/
  if ('cache' in request) {
    return request;
  }

  // If {cache: 'reload'} didn't have any effect, append a cache-busting URL parameter instead.
  let bustedUrl = new URL(url, self.location.href);
  bustedUrl.search += (bustedUrl.search ? '&' : '') + 'cachebust=' + Date.now();
  return new Request(bustedUrl);
}

// Cache the offline page during install phase of the service worker
self.addEventListener('install', event => {
  event.waitUntil(
    fetch(createCacheBustedRequest('/api/1/template/offline')).then(function(response) {
      return caches.open('hasjob-offline').then(function(cache) {
        return cache.put('offline', response);
      });
    })
  );
});
