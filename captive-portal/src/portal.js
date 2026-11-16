(function () {
  'use strict';
  // Native DOM only. No persistent browser storage, external assets or frameworks.
  var apiBase = document.querySelector('meta[name="portal-api-base"]').content,
    authBase = document.querySelector('meta[name="portal-auth-base"]').content,
    csrf = '', identity = null, categories = [], config = {survey: {}},
    selected = '', generation = 0, seen = {}, sessionBusy = false;
  function el(id) { return document.getElementById(id); }
  function node(tag, text, className) {
    var item = document.createElement(tag);
    if (text !== undefined && text !== null) { item.textContent = String(text); }
    if (className) { item.className = className; }
    return item;
  }
  function clear(item) { while (item.firstChild) { item.removeChild(item.firstChild); } }
  function message(target, text, error) { target.textContent = text; target.classList.toggle('error', !!error); }
  function errorText(body) {
    if (typeof body === 'string') { return body.slice(0, 500); }
    if (body && typeof body.detail === 'string') { return body.detail; }
    if (body && typeof body === 'object') {
      return Object.keys(body).map(function (key) { return key + ': ' + (Array.isArray(body[key]) ? body[key].join(' ') : String(body[key])); }).join(' ').slice(0, 500);
    }
    return 'No se pudo completar la petición. Inténtalo de nuevo.';
  }
  function request(url, method, data, callback) {
    var completed = false, timer;
    function finish(error, body, status) {
      if (completed) { return; } completed = true; window.clearTimeout(timer); callback(error, body, status);
    }
    var headers = {'Accept': 'application/json'};
    if (method !== 'GET') { headers['Content-Type'] = 'application/json'; headers['X-CSRFToken'] = csrf; }
    if (window.fetch && window.AbortController) {
      var controller = new window.AbortController();
      timer = window.setTimeout(function () { controller.abort(); finish('El servicio tardó demasiado. Inténtalo de nuevo.'); }, 8000);
      window.fetch(url, {method: method, credentials: 'include', headers: headers,
        body: data === null ? undefined : JSON.stringify(data), signal: controller.signal, cache: 'no-store'})
        .then(function (response) {
          return response.text().then(function (text) {
            var body; try { body = JSON.parse(text); } catch (_) { body = null; }
            finish(response.ok ? null : (body ? errorText(body) : 'El servicio no está disponible en este momento.'), body, response.status);
          });
        }).catch(function () { finish('No se pudo conectar al servicio. Comprueba la conexión y vuelve a intentarlo.'); });
    } else {
      // Older captive browsers: XHR has its own timeout, no Promise/fetch polyfill.
      var xhr = new window.XMLHttpRequest();
      xhr.open(method, url, true); xhr.timeout = 8000;
      xhr.withCredentials = true;
      Object.keys(headers).forEach(function (key) { xhr.setRequestHeader(key, headers[key]); });
      xhr.onload = function () {
        var body; try { body = JSON.parse(xhr.responseText); } catch (_) { body = null; }
        finish(xhr.status >= 200 && xhr.status < 300 ? null : (body ? errorText(body) : 'El servicio no está disponible en este momento.'), body, xhr.status);
      };
      xhr.onerror = function () { finish('No se pudo conectar al servicio. Comprueba la conexión.'); };
      xhr.ontimeout = function () { finish('El servicio tardó demasiado. Inténtalo de nuevo.'); };
      xhr.send(data === null ? null : JSON.stringify(data));
    }
  }
  function setSession(body) {
    identity = body.authenticated ? body.identity : null;
    if (body.csrfToken) { csrf = body.csrfToken; }
    el('login-form').hidden = !!identity; el('session').hidden = !identity;
    if (identity) {
      el('visitor-name').textContent = identity.full_name;
      el('visitor-type').textContent = 'DEMO · ' + identity.user_type;
      el('avatar').textContent = identity.full_name.slice(0, 1).toUpperCase();
    }
    if (body.mode === 'institutional') {
      el('demo-note').textContent = 'Integración institucional pendiente del contrato AGA_AUTH y pfSense. Este entorno no concede acceso a Internet.';
      el('login-title').textContent = 'Acceso institucional';
    }
  }
  function session(callback) {
    request(authBase + '/portal-auth/session', 'GET', null, function (error, body) {
      if (!error && body) { setSession(body); track('portal'); }
      if (callback) { callback(error); }
    });
  }
  function track(section, content) {
    var key = section + ':' + (content || 'section');
    if (!csrf || seen[key]) { return; }
    seen[key] = true;
    var body = {section: section}; if (content) { body.content = content; }
    request(apiBase + '/api/vistas', 'POST', body, function () {});
  }
  function safeLink(value) {
    if (typeof value !== 'string' || !/^https?:\/\//i.test(value) || /[\u0000-\u0020\u007f]/.test(value)) { return null; }
    var anchor = document.createElement('a'); anchor.href = value;
    return /^(https?:)$/.test(anchor.protocol) && anchor.hostname && !/@/.test(value.split('/')[2]) ? anchor.href : null;
  }
  function link(parent, label, value) {
    var url = safeLink(value); if (!url) { return; }
    var anchor = node('a', label + ' ↗', 'btn btn-outline');
    anchor.href = url; anchor.target = '_blank'; anchor.rel = 'noopener noreferrer';
    anchor.setAttribute('aria-label', label + ' (abre otra ventana)'); parent.appendChild(anchor);
  }
  function date(value) {
    if (!value) { return ''; }
    var d = new Date(value);
    if (isNaN(d.getTime())) { return ''; }
    try { return d.toLocaleString('es-CU', {year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'America/Havana'}); }
    catch (_) { return d.toLocaleString(); }
  }
  function empty(text) {
    clear(el('content')); var block = node('div', null, 'empty');
    block.appendChild(node('h3', text)); block.appendChild(node('p', 'Puedes consultar otra sección o actualizar la información.'));
    el('content').appendChild(block);
  }
  function survey(parent, item) {
    var definition = item.details || {};
    if (definition.external_url) {
      parent.appendChild(node('p', 'Esta encuesta se responde en un sitio externo. No se ha comprobado su disponibilidad.'));
      link(parent, 'Abrir encuesta externa', definition.external_url); return;
    }
    var form = node('form', null, 'survey-form'), questions = definition.questions || [], fields = [];
    questions.forEach(function (q) {
      var group = node('fieldset'), legend = node('legend', q.text + (q.required ? ' *' : ' (opcional)'));
      group.appendChild(legend); var inputs = [];
      if (q.kind === 'open') {
        var label = node('label', 'Tu respuesta', 'form-label'), input = node('textarea', null, 'form-control');
        input.id = 'answer-' + item.id + '-' + q.id; label.htmlFor = input.id;
        input.maxLength = 4000; input.required = q.required; input.rows = 3;
        group.appendChild(label); group.appendChild(input); inputs.push(input);
        group.appendChild(node('small', 'Máximo 4000 caracteres. No incluyas datos personales.'));
      } else {
        (q.options || []).forEach(function (option) {
          var label = node('label', null, 'option'), input = node('input');
          input.type = q.kind === 'single' ? 'radio' : 'checkbox'; input.name = 'q-' + item.id + '-' + q.id;
          input.value = option.id; input.id = input.name + '-' + option.id; label.htmlFor = input.id;
          if (q.kind === 'single') { input.required = q.required; }
          label.appendChild(input); label.appendChild(node('span', option.text));
          group.appendChild(label); inputs.push(input);
        });
        if (q.kind === 'multiple') { group.appendChild(node('small', 'Puedes marcar varias opciones, hasta ' + (config.survey.max_options || 100) + '.')); }
      }
      form.appendChild(group); fields.push({question: q, inputs: inputs});
    });
    if (config.survey.vote_requires_auth) { form.appendChild(node('p', 'Esta encuesta requiere iniciar sesión en el portal.', 'text-muted')); }
    var submit = node('button', 'Enviar respuestas', 'btn btn-primary'), status = node('p', '', 'survey-message');
    submit.type = 'submit'; status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
    form.appendChild(submit); form.appendChild(status);
    var busy = false, submitted = false;
    form.addEventListener('submit', function (event) {
      event.preventDefault(); if (busy || submitted) { return; }
      if (config.survey.vote_requires_auth && !identity) {
        message(status, 'Inicia sesión antes de responder. Tus respuestas se conservan.', true); el('username').focus(); return;
      }
      var invalid = '', answers = [];
      fields.forEach(function (field) {
        var q = field.question, answer = {question: q.id, options: [], value: ''};
        if (q.kind === 'open') { answer.value = field.inputs[0].value.trim(); }
        else { field.inputs.forEach(function (input) { if (input.checked) { answer.options.push(Number(input.value)); } }); }
        if (q.required && !answer.options.length && !answer.value) { invalid = 'Completa todas las preguntas obligatorias.'; }
        if (answer.options.length > (config.survey.max_options || 100)) { invalid = 'Hay demasiadas opciones seleccionadas.'; }
        if (answer.value.length > 4000) { invalid = 'La respuesta abierta supera los 4000 caracteres.'; }
        answers.push(answer);
      });
      if (invalid) { message(status, invalid, true); return; }
      busy = true; submit.disabled = true; message(status, 'Enviando respuestas…');
      function send() {
        request(apiBase + '/api/encuestas/' + item.id + '/respuestas', 'POST', {answers: answers}, function (error, body, code) {
          busy = false;
          if (error) { submit.disabled = false; message(status, error + ' Tus respuestas se conservan.', true);
            if (code === 403) { session(); } return; }
          submitted = true; submit.disabled = true; submit.textContent = 'Respuesta enviada';
          fields.forEach(function (field) { field.inputs.forEach(function (input) { input.disabled = true; }); });
          message(status, body.detail || 'Respuesta recibida. Gracias por participar.');
        });
      }
      if (csrf) { send(); } else { session(function (error) { if (error) { busy = false; submit.disabled = false; message(status, error, true); } else { send(); } }); }
    });
    parent.appendChild(form);
  }
  function card(item, category) {
    var article = node('article', null, 'card content-card'), details = item.details || {};
    article.setAttribute('data-kind', item.type);
    article.appendChild(node('span', category.name, 'tag')); article.appendChild(node('h3', item.title));
    article.appendChild(node('p', item.description.length > 180 ? item.description.slice(0, 180) + '…' : item.description, 'preserve'));
    var metadata = [];
    if (details.area_name) { metadata.push(details.area_name); }
    if (details.event_at) { metadata.push('Inicio: ' + date(details.event_at)); }
    else if (item.starts_at) { metadata.push(date(item.starts_at)); }
    if (details.contact) { metadata.push('Contacto: ' + details.contact); }
    if (metadata.length) { article.appendChild(node('p', metadata.join(' · '), 'meta')); }
    var button = node('button', item.type === 'survey' ? 'Participar en la encuesta' : 'Ver información', 'btn btn-outline');
    button.type = 'button'; button.setAttribute('aria-expanded', 'false');
    var expanded = node('div', null, 'expanded'); expanded.hidden = true; expanded.id = 'content-' + item.id;
    button.setAttribute('aria-controls', expanded.id);
    expanded.appendChild(node('p', item.description, 'preserve'));
    link(expanded, 'Leer en el sitio de origen', details.external_url && item.type !== 'survey' ? details.external_url : null);
    link(expanded, 'Ver convocatoria', details.invitation_url);
    link(expanded, 'Acceder al servicio', details.access_url);
    if (details.access_url) { expanded.appendChild(node('p', 'El servicio puede requerir acceso a la red institucional.', 'text-muted')); }
    if (item.type === 'generic' && item.extra_fields) {
      var list = node('dl', null, 'extra');
      Object.keys(item.extra_fields).forEach(function (key) {
        var value = item.extra_fields[key];
        if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
          list.appendChild(node('dt', key)); list.appendChild(node('dd', String(value)));
        }
      }); expanded.appendChild(list);
    }
    if (item.type === 'survey') { survey(expanded, item); }
    button.addEventListener('click', function () {
      expanded.hidden = !expanded.hidden; button.setAttribute('aria-expanded', String(!expanded.hidden));
      button.textContent = expanded.hidden ? (item.type === 'survey' ? 'Participar en la encuesta' : 'Ver información') : 'Cerrar información';
      if (!expanded.hidden) { track(category.slug, item.id); }
    });
    article.appendChild(button); article.appendChild(expanded); return article;
  }
  function section(slug) {
    var category = categories.filter(function (c) { return c.slug === slug; })[0];
    if (!category) { return; } selected = slug;
    var epoch = ++generation;
    Array.prototype.forEach.call(el('navigation').querySelectorAll('[data-section]'), function (button) {
      if (button.getAttribute('data-section') === slug) { button.setAttribute('aria-current', 'page'); }
      else { button.removeAttribute('aria-current'); }
    });
    el('content').setAttribute('aria-busy', 'true'); clear(el('content'));
    message(el('content-status'), 'Cargando ' + category.name.toLowerCase() + '…');
    request(apiBase + '/api/' + encodeURIComponent(slug), 'GET', null, function (error, items) {
      if (epoch !== generation) { return; }
      el('content').setAttribute('aria-busy', 'false');
      if (error || !Array.isArray(items)) {
        message(el('content-status'), 'No se pudo cargar la información institucional en este momento.', true);
        empty('Información no disponible'); return;
      }
      message(el('content-status'), category.name + ' · ' + items.length + (items.length === 1 ? ' publicación' : ' publicaciones'));
      clear(el('content'));
      if (!items.length) { empty('No hay publicaciones disponibles'); }
      else {
        var list = node('div', null, 'content-list');
        items.forEach(function (item) { list.appendChild(card(item, category)); }); el('content').appendChild(list);
      }
      track(slug);
    });
  }
  function refresh() {
    var epoch = ++generation; el('refresh').disabled = true;
    message(el('content-status'), 'Actualizando información…');
    // Config and category discovery are separate from all authentication requests.
    request(apiBase + '/api/config', 'GET', null, function (error, body) {
      if (epoch !== generation) { el('refresh').disabled = false; return; }
      if (error || !body || !Array.isArray(body.sections)) { failed(); return; }
      config = body;
      if (config.presentation) {
        if (config.presentation.wifi_label) { el('network-label').textContent = config.presentation.wifi_label; }
        if (config.presentation.welcome_text) { el('welcome-text').textContent = config.presentation.welcome_text; }
      }
      request(apiBase + '/api/categorias?include_contents=false', 'GET', null, function (error, discovered) {
        if (epoch !== generation) { el('refresh').disabled = false; return; }
        if (error || !Array.isArray(discovered)) { failed(); return; }
        categories = discovered.filter(function (category) {
          return /^[a-zA-Z0-9_-]+$/.test(category.slug) && config.sections.some(function (enabled) { return enabled.id === category.id; });
        });
        var navigation = el('navigation');
        Array.prototype.slice.call(navigation.querySelectorAll('[data-section]')).forEach(function (button) { navigation.removeChild(button); });
        categories.forEach(function (category) {
          var button = node('button', category.name, 'nav-link'); button.type = 'button'; button.setAttribute('data-section', category.slug);
          button.addEventListener('click', function () { section(category.slug); }); navigation.appendChild(button);
        });
        el('refresh').disabled = false;
        if (!categories.length) { selected = ''; clear(el('content')); empty('No hay secciones habilitadas'); message(el('content-status'), 'El inicio de sesión sigue disponible.'); el('content').setAttribute('aria-busy', 'false'); return; }
        section(categories.some(function (c) { return c.slug === selected; }) ? selected : categories[0].slug);
      });
    });
    function failed() {
      el('refresh').disabled = false; el('content').setAttribute('aria-busy', 'false');
      message(el('content-status'), 'No se pudo cargar la información institucional en este momento.', true);
      // Do not continue displaying content whose visibility cannot be refreshed.
      empty('Información no disponible');
    }
  }
  el('login-link').addEventListener('click', function () { el('login').focus(); track('login'); });
  el('refresh').addEventListener('click', refresh);
  el('login-form').addEventListener('submit', function (event) {
    event.preventDefault(); if (sessionBusy) { return; }
    if (!el('username').value.trim() || !el('password').value) { message(el('login-message'), 'Completa el usuario y la contraseña.', true); return; }
    sessionBusy = true; el('login-submit').disabled = true; message(el('login-message'), 'Validando cuenta…');
    function send() {
      var password = el('password').value; el('password').value = '';
      request(authBase + '/portal-auth/session', 'POST', {username: el('username').value.trim(), password: password}, function (error, body) {
        sessionBusy = false; el('login-submit').disabled = false;
        if (error) { message(el('login-message'), error, true); return; }
        setSession(body); message(el('login-message'), 'Sesión iniciada. Gracias por conectarte.');
      });
    }
    if (csrf) { send(); } else { session(function (error) { if (error) { sessionBusy = false; el('login-submit').disabled = false; message(el('login-message'), error, true); } else { send(); } }); }
  });
  el('logout').addEventListener('click', function () {
    if (sessionBusy) { return; } sessionBusy = true; el('logout').disabled = true;
    request(authBase + '/portal-auth/logout', 'POST', {}, function (error) {
      sessionBusy = false; el('logout').disabled = false;
      if (error) { message(el('login-message'), error, true); return; }
      setSession({authenticated: false}); message(el('login-message'), 'Sesión cerrada.'); session();
    });
  });
  // Session expiry is checked without re-rendering forms or losing survey drafts.
  window.setInterval(function () { if (!document.hidden && !sessionBusy) { session(); } }, 60000);
  document.addEventListener('visibilitychange', function () { if (!document.hidden && !sessionBusy) { session(); } });
  session(function (error) { if (error) { message(el('login-message'), 'El servicio de autenticación no está disponible. Puedes volver a intentarlo desde el formulario.', true); } });
  refresh();
}());
