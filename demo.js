// 🧪 데모 반 (?demo=1) — 진짜 Firebase 대신 브라우저 안 가짜 DB로 돌아간다.
//    진짜 반 데이터는 절대 건드리지 않음. 데이터는 이 브라우저의 localStorage('sinliDemoDB')에만 저장.
//    초기화: 주소에 ?demo=1&reset=1
(function(){
    var REAL = window.localStorage, KEY = 'sinliDemoDB', UID = 'demo-teacher', CID = 'DEMO';
    // 진짜 반의 저장값(classRoomName 등)과 섞이지 않게 localStorage를 'demo:' 접두어로 분리
    var shim = {
        getItem: function(k){ return REAL.getItem('demo:' + k); },
        setItem: function(k, v){ REAL.setItem('demo:' + k, String(v)); },
        removeItem: function(k){ REAL.removeItem('demo:' + k); },
        clear: function(){ Object.keys(REAL).forEach(function(k){ if(k.indexOf('demo:') === 0) REAL.removeItem(k); }); },
        key: function(i){ return Object.keys(REAL).filter(function(k){ return k.indexOf('demo:') === 0; }).map(function(k){ return k.slice(5); })[i] || null; },
        get length(){ return Object.keys(REAL).filter(function(k){ return k.indexOf('demo:') === 0; }).length; }
    };
    try { Object.defineProperty(window, 'localStorage', { value: shim, configurable: true }); } catch(e){}

    function clone(v){ return v === undefined ? null : JSON.parse(JSON.stringify(v)); }
    function norm(p){ return String(p || '').split('/').filter(Boolean); }
    function prune(v){
        if(v === null || v === undefined) return null;
        if(typeof v !== 'object') return v;
        var o = {}, n = 0;
        Object.keys(v).forEach(function(k){ var c = prune(v[k]); if(c !== null){ o[k] = c; n++; } });
        return n ? o : null;
    }

    var NAMES = ['김하늘','이준서','박서연','최도윤','정하은','강민준','조지우','윤서준','장예린','임시우','한소율','오지호','서다인','신우진','권나은','황태민','안채원','송현우','류지안','전민서','홍건우','문아린','배준혁','노유나'];
    function seed(){
        var roster = [], names = [], students = {}, jobs = ['knight','mage','priest','archer','bard'];
        var armors = ['a_gym','a_cloth','a_soccer','a_leather','a_dobok','a_chain','a_robe','a_ninja','a_knight'];
        NAMES.forEach(function(nm, i){
            var n = i + 1, g = (i % 2) ? '여' : '남';
            roster.push(n + ' ' + g); names.push(n + ' ' + nm + ' ' + g);
            var xp = 40 + ((i * 137) % 900);
            students[n] = { xp: xp, pw: '123456' };
            if(xp >= 100) students[n].job = jobs[i % 5];
            if(i % 3 === 0) students[n].equip = { armor: armors[i % armors.length] };
        });
        var t = Date.now(), r = {};
        r['users/' + UID + '/classes/' + CID] = 'owner';
        r['rooms/' + CID + '/_meta'] = { name: '🧪 데모반 (연습용)', ownerUid: UID, createdAt: t, code: 'DEMO01' };
        r['rooms/' + CID + '/_members/' + UID] = { role: 'owner', at: t };
        r['rooms/' + CID + '/settings/dashboardDefaults'] = { className: '🧪 데모반', roster: roster.join('\n') };
        r['rooms/' + CID + '/settings/rosterNames'] = names.join('\n');
        r['rooms/' + CID + '/rpg/students'] = students;
        r['studentCodes/DEMO01'] = CID;
        var root = {};
        Object.keys(r).forEach(function(p){ setAt(root, norm(p), r[p]); });
        return root;
    }
    function getAt(root, parts){ var c = root; for(var i = 0; i < parts.length; i++){ if(c === null || typeof c !== 'object') return null; c = c[parts[i]]; } return c === undefined ? null : c; }
    function setAt(root, parts, val){
        if(!parts.length) return;
        var c = root;
        for(var i = 0; i < parts.length - 1; i++){ if(c[parts[i]] === null || typeof c[parts[i]] !== 'object') c[parts[i]] = {}; c = c[parts[i]]; }
        if(val === null || val === undefined) delete c[parts[parts.length - 1]]; else c[parts[parts.length - 1]] = clone(val);
    }

    var tree;
    try { if(/[?&]reset=1/.test(location.search)) REAL.removeItem(KEY); tree = JSON.parse(REAL.getItem(KEY) || 'null'); } catch(e){ tree = null; }
    if(!tree){ tree = seed(); }
    var saveT = null;
    function save(){ clearTimeout(saveT); saveT = setTimeout(function(){ try { REAL.setItem(KEY, JSON.stringify(prune(tree) || {})); } catch(e){} }, 200); }
    save();

    var listeners = []; // {path, cb}
    function fire(changed){
        var cp = changed.join('/');
        listeners.slice().forEach(function(l){
            var lp = l.parts.join('/');
            if(cp === lp || cp.indexOf(lp + '/') === 0 || lp.indexOf(cp + '/') === 0 || lp === '' || cp === ''){
                setTimeout(function(){ if(listeners.indexOf(l) >= 0) try { l.cb(new Snap(l.parts, getAt(tree, l.parts))); } catch(e){ console.error(e); } }, 0);
            }
        });
        save();
    }
    function write(parts, val){ setAt(tree, parts, val); var p = prune(tree); tree = p || {}; fire(parts); }

    function Snap(parts, v){ this._p = parts; this._v = clone(v); this.key = parts.length ? parts[parts.length - 1] : null; this.ref = new Ref(parts); }
    Snap.prototype.val = function(){ return clone(this._v); };
    Snap.prototype.exists = function(){ return this._v !== null && this._v !== undefined; };
    Snap.prototype.child = function(p){ var v = this._v; return new Snap(this._p.concat(norm(p)), (v && typeof v === 'object') ? getAt(v, norm(p)) : null); };
    Snap.prototype.hasChild = function(p){ return this.child(p).exists(); };
    Snap.prototype.numChildren = function(){ return (this._v && typeof this._v === 'object') ? Object.keys(this._v).length : 0; };
    Snap.prototype.hasChildren = function(){ return this.numChildren() > 0; };
    Snap.prototype.forEach = function(fn){ var v = this._v, self = this; if(!v || typeof v !== 'object') return false; return Object.keys(v).some(function(k){ return fn(new Snap(self._p.concat([k]), v[k])) === true; }); };
    Snap.prototype.toJSON = function(){ return this.val(); };

    var lastPush = 0, PC = '-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz';
    function pushKey(){ var t = Math.max(Date.now(), lastPush + 1); lastPush = t; var s = ''; for(var i = 0; i < 8; i++){ s = PC.charAt(t % 64) + s; t = Math.floor(t / 64); } for(var j = 0; j < 12; j++) s += PC.charAt(Math.floor(Math.random() * 64)); return s; }

    function Ref(parts){ this._p = parts; this.key = parts.length ? parts[parts.length - 1] : null; this.path = parts.join('/'); }
    Ref.prototype.child = function(p){ return new Ref(this._p.concat(norm(p))); };
    Object.defineProperty(Ref.prototype, 'parent', { get: function(){ return this._p.length ? new Ref(this._p.slice(0, -1)) : null; } });
    Object.defineProperty(Ref.prototype, 'root', { get: function(){ return new Ref([]); } });
    Ref.prototype.toString = function(){ return 'demo://' + this.path; };
    Ref.prototype.set = function(v, cb){ write(this._p, v); if(cb) setTimeout(function(){ cb(null); }, 0); return Promise.resolve(); };
    Ref.prototype.remove = function(cb){ return this.set(null, cb); };
    Ref.prototype.update = function(obj, cb){
        var self = this;
        Object.keys(obj || {}).forEach(function(k){ setAt(tree, self._p.concat(norm(k)), obj[k]); });
        tree = prune(tree) || {};
        Object.keys(obj || {}).forEach(function(k){ fire(self._p.concat(norm(k))); });
        if(cb) setTimeout(function(){ cb(null); }, 0);
        return Promise.resolve();
    };
    Ref.prototype.push = function(v, cb){
        var r = this.child(pushKey());
        var p = (v === undefined) ? Promise.resolve(r) : r.set(v, cb).then(function(){ return r; });
        r.then = p.then.bind(p); r.catch = p.catch.bind(p);
        return r;
    };
    Ref.prototype.once = function(ev, cb, err){
        var s = new Snap(this._p, getAt(tree, this._p));
        if(typeof cb === 'function') setTimeout(function(){ cb(s); }, 0);
        return Promise.resolve(s);
    };
    Ref.prototype.on = function(ev, cb){
        if(ev !== 'value') { console.warn('[demo] on(' + ev + ') 미지원'); return cb; }
        var l = { parts: this._p, cb: cb }; listeners.push(l);
        var self = this; setTimeout(function(){ if(listeners.indexOf(l) >= 0) cb(new Snap(self._p, getAt(tree, self._p))); }, 0);
        return cb;
    };
    Ref.prototype.off = function(ev, cb){
        var lp = this.path;
        listeners = listeners.filter(function(l){ return !(l.parts.join('/') === lp && (!cb || l.cb === cb)); });
    };
    Ref.prototype.transaction = function(fn, onDone){
        var cur = getAt(tree, this._p), nv = fn(clone(cur)), self = this;
        var committed = nv !== undefined;
        if(committed) write(this._p, nv);
        var snap = new Snap(this._p, getAt(tree, this._p));
        if(onDone) setTimeout(function(){ onDone(null, committed, snap); }, 0);
        return Promise.resolve({ committed: committed, snapshot: snap });
    };
    Ref.prototype.onDisconnect = function(){ return { set: function(){ return Promise.resolve(); }, remove: function(){ return Promise.resolve(); }, update: function(){ return Promise.resolve(); }, cancel: function(){ return Promise.resolve(); } }; };

    var user = { uid: UID, displayName: '데모', email: 'demo@example.com', isAnonymous: false };
    var authCbs = [], signedIn = REAL.getItem('demo:__signedOut') !== '1';
    var auth = {
        get currentUser(){ return signedIn ? user : null; },
        onAuthStateChanged: function(cb){ authCbs.push(cb); setTimeout(function(){ cb(signedIn ? user : null); }, 0); return function(){ authCbs = authCbs.filter(function(c){ return c !== cb; }); }; },
        signOut: function(){ signedIn = false; REAL.setItem('demo:__signedOut', '1'); authCbs.forEach(function(c){ c(null); }); return Promise.resolve(); },
        signInWithPopup: function(){ signedIn = true; REAL.removeItem('demo:__signedOut'); authCbs.forEach(function(c){ c(user); }); return Promise.resolve({ user: user }); },
        signInWithEmailAndPassword: function(){ return auth.signInWithPopup(); },
        createUserWithEmailAndPassword: function(){ return auth.signInWithPopup(); },
        sendPasswordResetEmail: function(){ return Promise.resolve(); },
        signInAnonymously: function(){ return Promise.resolve({ user: { uid: 'demo-student', isAnonymous: true } }); },
        setPersistence: function(){ return Promise.resolve(); }
    };

    window.DEMO = { db: { ref: function(p){ return new Ref(norm(p)); } }, auth: auth, dump: function(){ return clone(tree); }, reset: function(){ REAL.removeItem(KEY); location.reload(); } };
    // 처음 들어오면 데모반으로 바로 입장
    if(!shim.getItem('classRoomName')){ shim.setItem('classRoomName', CID); shim.setItem('classRole', 'owner'); }
    document.addEventListener('DOMContentLoaded', function(){
        var b = document.createElement('div');
        b.innerHTML = '🧪 데모반 — 연습용 가짜 데이터 (진짜 반과 무관) · <a href="?demo=1&reset=1" style="color:#fff;text-decoration:underline;">처음 상태로</a> · <a href="./" style="color:#fff;text-decoration:underline;">나가기</a>';
        b.style.cssText = 'position:fixed;left:50%;bottom:6px;transform:translateX(-50%);z-index:2147483000;background:rgba(230,81,0,.92);color:#fff;font:700 12px Pretendard,sans-serif;padding:5px 14px;border-radius:14px;pointer-events:auto;';
        document.body.appendChild(b);
    });
})();
