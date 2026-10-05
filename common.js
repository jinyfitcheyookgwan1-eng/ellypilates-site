// Always land at the top of a newly-loaded page (never keep a leftover
// scroll position from the previous page), except when the URL points at
// a specific in-page anchor (e.g. programs.html#program), which should
// still scroll to that section as intended.
(function(){
  if('scrollRestoration' in history){
    history.scrollRestoration = 'manual';
  }
  if(!location.hash){
    window.scrollTo(0, 0);
  }
})();

// 영상 지연 재생: 처음에는 포스터만 보여주고(preload="none"), 화면에 들어올 때 재생을 시작하고
// 화면에서 벗어나면 일시정지한다. 반복 재생·음소거·소리 켜기 버튼 동작은 그대로 유지된다.
(function(){
  var vids = [].slice.call(document.querySelectorAll('video[data-lazy-play]'));
  if(!vids.length) return;
  function play(v){
    var p = v.play();
    if(p && p.catch){ p.catch(function(){}); }
  }
  if(!('IntersectionObserver' in window)){
    vids.forEach(play);
    return;
  }
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(e.isIntersecting){ play(e.target); }
      else { e.target.pause(); }
    });
  }, { rootMargin: '150px 0px', threshold: 0.01 });
  vids.forEach(function(v){ io.observe(v); });
})();

(function(){
  document.querySelectorAll('.av-player').forEach(function(wrap){
    var video = wrap.querySelector('video');
    var toggle = wrap.querySelector('.hero-sound-toggle');
    if(!video || !toggle) return;
    toggle.addEventListener('click', function(){
      video.muted = !video.muted;
      if(!video.muted){
        video.play().catch(function(){});
      }
      var on = !video.muted;
      toggle.setAttribute('aria-pressed', on ? 'true' : 'false');
      toggle.setAttribute('aria-label', on ? '영상 소리 끄기' : '영상 소리 켜기');
      toggle.querySelector('.hero-sound-label').textContent = on ? '소리 끄기' : '소리 켜기';
    });
  });
})();

document.querySelectorAll('.copy-btn').forEach(function(btn){
  btn.addEventListener('click', function(){
    var text = btn.getAttribute('data-copy');
    function done(){
      btn.setAttribute('data-copied','true');
      setTimeout(function(){ btn.removeAttribute('data-copied'); }, 1600);
    }
    try{
      navigator.clipboard.writeText(text).then(done).catch(function(){
        fallbackCopy(text); done();
      });
    }catch(e){
      fallbackCopy(text); done();
    }
    function fallbackCopy(t){
      var ta = document.createElement('textarea');
      ta.value = t;
      ta.style.position='fixed';
      ta.style.opacity='0';
      document.body.appendChild(ta);
      ta.select();
      try{ document.execCommand('copy'); }catch(e){}
      document.body.removeChild(ta);
    }
  });
});

(function(){
  var items = window.GALLERY_ITEMS;
  var lightbox = document.getElementById('lightbox');
  if(!items || !lightbox) return;

  var imgEl = document.getElementById('lightboxImg');
  var countEl = document.getElementById('lightboxCount');
  var triggers = document.querySelectorAll('.gallery-item');
  var current = 0;
  var lastFocused = null;

  function show(i){
    current = (i + items.length) % items.length;
    var it = items[current];
    imgEl.src = it.src;
    imgEl.alt = it.alt;
    countEl.textContent = (current + 1) + ' / ' + items.length;
  }
  function open(i){
    lastFocused = document.activeElement;
    show(i);
    lightbox.classList.add('open');
    lightbox.setAttribute('aria-hidden','false');
    document.body.style.overflow = 'hidden';
  }
  function close(){
    lightbox.classList.remove('open');
    lightbox.setAttribute('aria-hidden','true');
    document.body.style.overflow = '';
    if(lastFocused && lastFocused.focus) lastFocused.focus();
  }

  triggers.forEach(function(btn){
    btn.addEventListener('click', function(){
      var idx = parseInt(btn.getAttribute('data-index'), 10) || 0;
      open(idx);
    });
  });
  lightbox.querySelectorAll('[data-lb-close]').forEach(function(el){
    el.addEventListener('click', close);
  });
  lightbox.querySelector('[data-lb-prev]').addEventListener('click', function(){ show(current - 1); });
  lightbox.querySelector('[data-lb-next]').addEventListener('click', function(){ show(current + 1); });

  document.addEventListener('keydown', function(e){
    if(!lightbox.classList.contains('open')) return;
    if(e.key === 'Escape') close();
    else if(e.key === 'ArrowLeft') show(current - 1);
    else if(e.key === 'ArrowRight') show(current + 1);
  });
})();

(function(){
  var root = document.querySelector('.faq-accordion');
  if(!root) return;
  root.querySelectorAll('.faq-accordion-item').forEach(function(item){
    var trigger = item.querySelector('.faq-accordion-trigger');
    if(!trigger) return;
    trigger.addEventListener('click', function(){
      var isOpen = item.classList.contains('open');
      if(isOpen){
        item.classList.remove('open');
        trigger.setAttribute('aria-expanded', 'false');
      }else{
        item.classList.add('open');
        trigger.setAttribute('aria-expanded', 'true');
      }
    });
  });
})();

(function(){
  var toggle = document.getElementById('navToggle');
  var panel = document.getElementById('mobileNav');
  if(!toggle || !panel) return;

  function open(){
    panel.classList.add('open');
    panel.setAttribute('aria-hidden','false');
    toggle.setAttribute('aria-expanded','true');
    document.body.style.overflow = 'hidden';
  }
  function close(){
    panel.classList.remove('open');
    panel.setAttribute('aria-hidden','true');
    toggle.setAttribute('aria-expanded','false');
    document.body.style.overflow = '';
  }

  toggle.addEventListener('click', function(){
    if(panel.classList.contains('open')) close(); else open();
  });
  panel.querySelectorAll('[data-mnav-close]').forEach(function(el){
    el.addEventListener('click', close);
  });
  panel.querySelectorAll('.mobile-nav-links a').forEach(function(a){
    a.addEventListener('click', close);
  });
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape' && panel.classList.contains('open')) close();
  });
})();

// iOS Safari ignores :hover/:active on tap unless a touch listener is
// registered somewhere on the page. This enables tap feedback (e.g. the
// footer channel icons' press state) across the whole site.
document.addEventListener('touchstart', function(){}, {passive: true});

// Home hero: make the gold "8년의 시간…" line exactly as wide as the widest
// line of the H1 above it. Width-matching depends on the real web fonts, so it
// is measured at runtime (after fonts load) instead of hard-coding sizes.
(function(){
  var h1 = document.querySelector('.home-hero-content h1');
  var stat = document.querySelector('.home-hero-content .hero-stat');
  if(!h1 || !stat) return;

  function widestLine(el){
    var r = document.createRange();
    r.selectNodeContents(el);
    var w = 0;
    Array.prototype.forEach.call(r.getClientRects(), function(rc){
      if(rc.width > w) w = rc.width;
    });
    return w;
  }

  function fit(){
    stat.style.fontSize = '';
    // phones keep the original fixed-size, wrapping line (CSS only)
    if(window.matchMedia('(max-width:640px)').matches){ stat.style.whiteSpace = ''; return; }
    stat.style.whiteSpace = 'nowrap';
    var target = widestLine(h1);
    var avail = stat.parentElement.clientWidth;
    var natural = widestLine(stat);
    var size = parseFloat(getComputedStyle(stat).fontSize);
    if(!target || !natural || !size){ stat.style.whiteSpace = ''; return; }
    var next = size * Math.min(target, avail) / natural;
    next = Math.max(14, Math.min(next, 38));
    stat.style.fontSize = next.toFixed(2) + 'px';
    // refine a few times (text widths are not perfectly linear in font-size)
    var goal = Math.min(target, avail), best = next, bestErr = Math.abs(widestLine(stat) - goal);
    var cur = next;
    for(var i = 0; i < 4 && bestErr > 1; i++){
      var w = widestLine(stat);
      if(!w) break;
      cur = Math.max(14, Math.min(cur * goal / w, 38));
      stat.style.fontSize = cur.toFixed(2) + 'px';
      var err = Math.abs(widestLine(stat) - goal);
      if(err < bestErr){ bestErr = err; best = cur; }
    }
    stat.style.fontSize = best.toFixed(2) + 'px';
  }

  var t;
  function schedule(){ clearTimeout(t); t = setTimeout(fit, 60); }
  fit();
  if(document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
  window.addEventListener('load', fit);
  window.addEventListener('resize', schedule);
})();
