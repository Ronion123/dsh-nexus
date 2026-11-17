window.__ModuleLoader__.load({
  id: 'dsh-nexus',
  factory: function makeFactory() {
    return function build(require) {
      /**
       * dsh-nexus client half.
       *
       * dsh-pet keeps whatever clip a drag began with and never flips `facing`
       * from cursor motion, so a pet thrown left still looks like it flies right.
       * This module watches pointer motion on each rendered pet and drives
       * `facing` through the public `/anim` endpoint, which accepts `facing` and
       * is the supported control channel. The directional flight clips ship in
       * the character pack.
       *
       * Fully defensive: without DOM, without dsh-pet, or with a renamed route it
       * does nothing instead of throwing inside the slot.
       */
      const module = { exports: {} }
      const ROUTE = '/dsh-pet-7340'
      const CLIP_LEFT = '拖拽-飞行向左'
      const CLIP_RIGHT = '拖拽-飞行向右'
      const MIN_DX = 6
      const RESCAN_MS = 2000

      let petIds = null
      let fetching = false

      function loadPetIds(done) {
        if (petIds !== null) {
          done(petIds)
          return
        }
        if (fetching) return
        fetching = true
        fetch(ROUTE + '/config')
          .then(function (r) { return r.ok ? r.json() : null })
          .then(function (cfg) {
            const ids = []
            if (cfg && typeof cfg === 'object') {
              const entries = Object.keys(cfg).map(function (k) { return cfg[k] })
              for (const entry of entries) {
                if (entry && Array.isArray(entry.pets)) {
                  for (const pet of entry.pets) {
                    if (pet && typeof pet.id === 'string' && pet.id) ids.push(pet.id)
                  }
                }
              }
            }
            petIds = ids
          })
          .catch(function () { petIds = [] })
          .then(function () { fetching = false; done(petIds) })
      }

      function attach(el, petId) {
        let dragging = false
        let lastX = null
        let lastFacing = null
        let pending = null

        function push(facing) {
          if (facing === lastFacing) return
          lastFacing = facing
          const name = facing === 'left' ? CLIP_LEFT : CLIP_RIGHT
          try {
            fetch(ROUTE + '/anim?pet=' + encodeURIComponent(petId) + '&surface=any', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json; charset=utf-8' },
              body: JSON.stringify({ name: name, facing: facing }),
              keepalive: true,
            }).catch(function () {})
          } catch (e) {
            /* offline: leave the sprite alone */
          }
        }

        function down() {
          dragging = true
          lastX = null
        }
        function move(ev) {
          if (!dragging) return
          if (lastX === null) {
            lastX = ev.clientX
            return
          }
          const dx = ev.clientX - lastX
          lastX = ev.clientX
          if (Math.abs(dx) < MIN_DX) return
          if (pending !== null) return
          pending = requestAnimationFrame(function () {
            pending = null
            push(dx < 0 ? 'left' : 'right')
          })
        }
        function up() {
          dragging = false
          lastX = null
        }

        el.addEventListener('pointerdown', down, true)
        el.addEventListener('pointermove', move, true)
        window.addEventListener('pointerup', up, true)
        window.addEventListener('pointercancel', up, true)

        return function cleanup() {
          el.removeEventListener('pointerdown', down, true)
          el.removeEventListener('pointermove', move, true)
          window.removeEventListener('pointerup', up, true)
          window.removeEventListener('pointercancel', up, true)
          if (pending !== null) cancelAnimationFrame(pending)
        }
      }

      function apply(ctx) {
        const cleanups = []
        const wired = new WeakSet()
        let timer = null
        let observer = null

        function scan() {
          const roots = document.querySelectorAll('.dsh-pet-root')
          if (!roots.length) return
          loadPetIds(function (ids) {
            let index = 0
            for (const el of roots) {
              if (wired.has(el)) {
                index += 1
                continue
              }
              const id = ids[index] || (ids.length === 1 ? ids[0] : null)
              index += 1
              if (!id) continue
              wired.add(el)
              cleanups.push(attach(el, id))
            }
          })
        }

        try {
          scan()
          timer = window.setInterval(scan, RESCAN_MS)
          observer = new MutationObserver(scan)
          observer.observe(document.body, { childList: true, subtree: true })
        } catch (e) {
          /* no DOM */
        }

        ctx.effect(
          function () {
            return function () {
              for (const c of cleanups) {
                try { c() } catch (e) { /* ignore */ }
              }
              if (timer !== null) window.clearInterval(timer)
              if (observer !== null) observer.disconnect()
            }
          },
          'dsh-nexus: directional flight',
        )
      }

      module.exports = {
        name: 'dsh-nexus',
        apply: apply,
      }
      return module.exports
    }
  },
})
