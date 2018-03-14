importScripts('https://unpkg.com/workbox-sw@2.1.2/build/importScripts/workbox-sw.prod.v2.1.2.js');

const workboxSW = new self.WorkboxSW({
  "cacheId": "hasjob",
  "skipWaiting": true,
  "clientsClaim": true
});

workboxSW.precache([]);

workboxSW.router.registerNavigationRoute("/");workboxSW.router.registerRoute(/^https?\:\/\/static.*/, workboxSW.strategies.networkFirst({
  "cacheName": "assets"
}), 'GET');

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

workboxSW.router.registerRoute('/', workboxSW.strategies.networkFirst({
  "cacheName": "routes"
}), 'GET');

workboxSW.router.registerRoute('/*', workboxSW.strategies.networkFirst({
  "cacheName": "routes"
}), 'GET');
