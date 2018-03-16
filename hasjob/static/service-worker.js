importScripts('https://unpkg.com/workbox-sw@2.1.2/build/importScripts/workbox-sw.prod.v2.1.2.js');

const workboxSW = new self.WorkboxSW({
  "cacheId": "hasjob",
  "skipWaiting": true,
  "clientsClaim": true
});

workboxSW.precache([
  {
    "url": "/static/build/css/stylesheet-app-css.252c175cf0268e5fe5c8.css",
    "revision": "4d69ae1ffaa574aef1281dc57414df39"
  },
  {
    "url": "/static/build/js/app.252c175cf0268e5fe5c8.js",
    "revision": "ee531064e82330054605f85bb7468442"
  },
  {
    "url": "/static/build/js/manifest.252c175cf0268e5fe5c8.js",
    "revision": "fe684bf23b9518850a7a3dd90492001d"
  },
  {
    "url": "/static/build/js/vendor.252c175cf0268e5fe5c8.js",
    "revision": "12a1ca8d2cb2caab35d21438cb595e94"
  }
]);

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

workboxSW.router.registerRoute(/^https?:\/\/fonts.gstatic.com\/*/, workboxSW.strategies.networkFirst({
  "cacheName": "fonts"
}), 'GET');

workboxSW.router.registerRoute('/', workboxSW.strategies.networkFirst({
  "cacheName": "routes"
}), 'GET');

workboxSW.router.registerRoute('/*', workboxSW.strategies.networkFirst({
  "cacheName": "routes"
}), 'GET');
