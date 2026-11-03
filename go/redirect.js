// [GO-LINK-1012] 기기별 스토어 자동 분기. 브라우저와 node 테스트 양쪽에서 쓴다.
(function (root) {
  function detect(ua, platform, maxTouch) {
    ua = ua || "";
    var ios = /iPhone|iPad|iPod/i.test(ua) ||
      ((platform === "MacIntel" || /Macintosh/.test(ua)) && (maxTouch || 0) > 1);
    if (ios) return "ios";
    if (/Android/i.test(ua)) return "android";
    return "other";
  }
  function cleanCode(search) {
    var m = /[?&]code=([^&#]*)/.exec(search || "");
    if (!m) return null;
    var c = decodeURIComponent(m[1].replace(/\+/g, " "))
      .replace(/[^A-Za-z0-9-]/g, "").slice(0, 24).toUpperCase();
    return c || null;
  }
  // utm 3종을 referrer 문자열로. 허용 문자만 남기고 인코딩 후 512자 이하일 때만 쓴다.
  function utmReferrer(search) {
    var keys = ["utm_source", "utm_medium", "utm_campaign"];
    var parts = [];
    for (var i = 0; i < keys.length; i++) {
      var m = new RegExp("[?&]" + keys[i] + "=([^&#]*)").exec(search || "");
      if (!m) continue;
      var v;
      try { v = decodeURIComponent(m[1].replace(/\+/g, " ")); } catch (e) { continue; }
      v = v.replace(/[^A-Za-z0-9_.\-]/g, "").slice(0, 64);
      if (v) parts.push(keys[i] + "=" + v);
    }
    var s = parts.join("&");
    return (s && encodeURIComponent(s).length <= 512) ? s : null;
  }
  // Play 이동 주소. cfg.referrer(추천코드 앱)는 기존 동작 그대로, 그 외 앱만 utm 을 붙인다.
  function playUrl(cfg, search) {
    var url = cfg.play;
    if (!url) return url;
    if (cfg.referrer) {
      var code = cleanCode(search);
      if (code) url += "&referrer=" + encodeURIComponent(code);
    } else {
      var u = utmReferrer(search);
      if (u) url += (url.indexOf("?") >= 0 ? "&" : "?") + "referrer=" + encodeURIComponent(u);
    }
    return url;
  }
  // 반환: 이동할 주소 (null 이면 이동 안 하고 버튼만)
  function pickTarget(cfg, ua, platform, maxTouch, search) {
    var d = detect(ua, platform, maxTouch);
    if (d === "ios") return cfg.appStore || null;
    if (d === "android") return playUrl(cfg, search);
    return null;
  }
  var api = { detect: detect, cleanCode: cleanCode, pickTarget: pickTarget, playUrl: playUrl, utmReferrer: utmReferrer };
  if (typeof module !== "undefined" && module.exports) { module.exports = api; return; }
  root.MungGo = api;
  var cfg = root.GO_CFG;
  if (!cfg) return;
  var d = detect(navigator.userAgent, navigator.platform, navigator.maxTouchPoints);
  var playBtn = document.getElementById("btnPlay");
  if (playBtn) {
    var pu = playUrl(cfg, location.search);
    if (pu !== cfg.play) playBtn.href = pu;
  }
  if (d === "ios" && !cfg.appStore) {
    var s = document.getElementById("soon"); if (s) s.hidden = false;
    return;
  }
  var t = pickTarget(cfg, navigator.userAgent, navigator.platform, navigator.maxTouchPoints, location.search);
  if (t) { var m = document.getElementById("moving"); if (m) m.hidden = false; location.replace(t); }
})(this);
