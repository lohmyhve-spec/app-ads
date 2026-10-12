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
  // 반환: 이동할 주소 (null 이면 이동 안 하고 버튼만)
  function pickTarget(cfg, ua, platform, maxTouch, search) {
    var d = detect(ua, platform, maxTouch);
    if (d === "ios") return cfg.appStore || null;
    if (d === "android") {
      var url = cfg.play;
      if (cfg.referrer) {
        var code = cleanCode(search);
        if (code) url += "&referrer=" + encodeURIComponent(code);
      }
      return url;
    }
    return null;
  }
  var api = { detect: detect, cleanCode: cleanCode, pickTarget: pickTarget };
  if (typeof module !== "undefined" && module.exports) { module.exports = api; return; }
  root.MungGo = api;
  var cfg = root.GO_CFG;
  if (!cfg) return;
  var d = detect(navigator.userAgent, navigator.platform, navigator.maxTouchPoints);
  var playBtn = document.getElementById("btnPlay");
  if (cfg.referrer && playBtn) {
    var c = cleanCode(location.search);
    if (c) playBtn.href = cfg.play + "&referrer=" + encodeURIComponent(c);
  }
  if (d === "ios" && !cfg.appStore) {
    var s = document.getElementById("soon"); if (s) s.hidden = false;
    return;
  }
  var t = pickTarget(cfg, navigator.userAgent, navigator.platform, navigator.maxTouchPoints, location.search);
  if (t) { var m = document.getElementById("moving"); if (m) m.hidden = false; location.replace(t); }
})(this);
