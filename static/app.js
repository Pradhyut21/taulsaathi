'use strict';

(() => {
  const $ = (id) => document.getElementById(id);
  const fieldNames = ['material', 'gross_kg', 'tare_kg', 'net_kg', 'rate_inr_per_kg'];
  const labels = { material: 'Material', gross_kg: 'Gross weight', tare_kg: 'Container weight', net_kg: 'Stated net weight', rate_inr_per_kg: 'Rate per kg' };
  const state = { configured: false, connected: false, busy: false, draft: null, source: 'typed', exampleId: null, transcription: null, liveVerified: false, audioURL: null };

  function error(message) {
    $('error-message').textContent = message;
    $('error-message').hidden = !message;
    if (message) $('error-message').scrollIntoView({ behavior: 'auto', block: 'center' });
  }

  async function request(path, options = {}) {
    const response = await fetch(path, { ...options, headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...options.headers } });
    if (!response.ok) {
      const body = await response.text();
      let message;
      try { const parsed = JSON.parse(body); message = parsed.error || parsed.message || body; } catch { message = body; }
      throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
    }
    return response;
  }

  async function json(path, payload) {
    const response = await request(path, payload === undefined ? {} : { method: 'POST', body: JSON.stringify(payload) });
    return response.json();
  }

  async function run(action, button, busyText) {
    if (state.busy) return;
    state.busy = true;
    error('');
    const oldChildren = button ? [...button.childNodes] : null;
    if (button && busyText) button.textContent = busyText;
    refreshControls();
    try { await action(); }
    catch (err) { error(err.message || 'The request could not be completed. Please try again.'); }
    finally {
      state.busy = false;
      if (button && busyText) button.replaceChildren(...oldChildren);
      refreshControls();
    }
  }

  function normalized(value) { return value === null || value === undefined ? '' : String(value); }
  function hasChanges() {
    if (!state.draft) return false;
    return fieldNames.some((field) => $(`field-${field}`).value.trim() !== normalized(state.draft.fields[field]));
  }
  function inputMismatch() {
    return Boolean(state.draft && ($('transcript').value.trim() !== state.draft.transcript.trim() || $('language').value !== state.draft.language));
  }
  function formatNumber(value, places = 3) {
    if (value === null || value === undefined || value === '') return '—';
    const number = Number(value);
    return Number.isFinite(number) ? number.toLocaleString('en-IN', { maximumFractionDigits: places }) : String(value);
  }

  function refreshControls() {
    $('create-draft').disabled = state.busy || !$('transcript').value.trim();
    $('clear-input').disabled = state.busy;
    $('language').disabled = state.busy;
    $('transcript').disabled = state.busy;
    $('audio-file').disabled = state.busy;
    $('transcribe').disabled = state.busy || !state.configured || !$('audio-file').files.length;
    document.querySelectorAll('.example-button').forEach((button) => { button.disabled = state.busy; });
    if (!state.draft) return;
    const dirty = hasChanges();
    const mismatch = inputMismatch();
    $('draft-input-note').hidden = !mismatch;
    $('record-status').textContent = mismatch ? 'Earlier input' : state.draft.status === 'confirmed' ? 'Confirmed' : 'Draft · review needed';
    $('record-status').className = `record-status ${!mismatch && state.draft.status === 'confirmed' ? 'confirmed' : 'draft'}`;
    $('unsaved-note').hidden = !dirty;
    fieldNames.forEach((field) => {
      const input = $(`field-${field}`);
      const changed = input.value.trim() !== normalized(state.draft.fields[field]);
      input.classList.toggle('dirty', changed);
      input.disabled = state.busy;
      document.querySelector(`[data-apply="${field}"]`).disabled = state.busy || !changed;
    });
    $('correction-reason').disabled = state.busy;
    $('transcript-reviewed').disabled = state.busy || dirty || mismatch;
    $('warning-reason').disabled = state.busy;
    $('resolve-warnings').disabled = state.busy || dirty || mismatch || !$('transcript-reviewed').checked || $('warning-reason').value.trim().length < 8;
    $('readback').disabled = state.busy || !state.configured || dirty || mismatch || Boolean((state.draft.issues || []).length);
    $('reviewed').disabled = state.busy || !state.draft.can_confirm || dirty || mismatch;
    $('confirm').disabled = state.busy || !state.draft.can_confirm || dirty || mismatch || !$('reviewed').checked || state.draft.status === 'confirmed';
    $('download-receipt').setAttribute('aria-disabled', String(dirty || mismatch || state.busy));
    if (dirty || mismatch || state.busy) {
      $('download-receipt').removeAttribute('href');
      $('download-receipt').tabIndex = -1;
    } else {
      $('download-receipt').href = `/api/receipt?id=${encodeURIComponent(state.draft.id)}`;
      $('download-receipt').tabIndex = 0;
    }
    $('print-record').disabled = state.busy || dirty || mismatch;
  }

  function sourceNote() {
    const note = $('source-note');
    note.classList.toggle('synthetic', state.source === 'synthetic');
    note.textContent = state.source === 'synthetic'
      ? 'Synthetic scenario · illustrative text, not a real user transaction'
      : state.source === 'gnani'
        ? 'Live Gnani transcript · check the text before creating a draft'
        : 'Typed input · no speech API call';
  }

  function updateConnection() {
    const badge = $('connection-badge');
    const dot = document.createElement('span');
    dot.className = 'dot';
    badge.replaceChildren(dot, document.createTextNode(state.liveVerified ? 'Live speech verified' : state.configured ? 'API key detected' : 'Local mode · no API key'));
    badge.className = `connection ${state.configured ? 'ready' : 'unavailable'}`;
    const banner = $('status-message');
    banner.className = `status-banner ${state.liveVerified ? 'live' : 'warning'}`;
    banner.textContent = state.liveVerified
      ? 'A live Gnani speech call succeeded in this session. Review the transcript and every critical number before confirming.'
      : state.configured
        ? 'A Gnani API key is configured. Live speech has not been verified in this session. Text scenarios run locally; speech buttons use credits.'
        : 'Local prototype mode. Typed and synthetic text scenarios work without credits. Configure a Gnani API key on the server to enable live speech.';
  }

  function renderDraft(draft) {
    state.draft = draft;
    $('empty-state').hidden = true;
    $('draft-content').hidden = false;
    $('reviewed').checked = false;
    $('transcript-reviewed').checked = false;
    $('warning-reason').value = '';
    $('correction-reason').value = '';
    const confirmed = draft.status === 'confirmed';
    $('record-status').textContent = confirmed ? 'Confirmed' : 'Draft · review needed';
    $('record-status').className = `record-status ${confirmed ? 'confirmed' : 'draft'}`;
    $('draft-id').textContent = `Record ${String(draft.id).slice(0, 10)}`;
    $('revision-label').textContent = `Revision ${draft.revision}`;
    $('draft-source').textContent = draft.source === 'synthetic' ? 'Synthetic scenario' : draft.source === 'gnani' ? 'Live Gnani transcript' : 'Typed input';
    $('issues-list').replaceChildren();
    (draft.issues || []).forEach((issue) => {
      const item = document.createElement('li');
      item.textContent = typeof issue === 'string' ? issue : issue.message || JSON.stringify(issue);
      $('issues-list').append(item);
    });
    $('issues-box').hidden = !(draft.issues || []).length;
    $('warning-review').hidden = !(draft.parse_issues || []).length;
    fieldNames.forEach((field) => { $(`field-${field}`).value = normalized(draft.fields[field]); });
    $('net-total').replaceChildren(document.createTextNode(formatNumber(draft.computed.net_kg)), unit(' kg'));
    $('rate-total').replaceChildren(document.createTextNode(`₹ ${formatNumber(draft.fields.rate_inr_per_kg, 2)}`), unit(' / kg'));
    $('amount-total').textContent = `₹ ${formatNumber(draft.computed.total_inr, 2)}`;
    $('readback-text').textContent = draft.readback_text || 'Resolve the missing details above to complete the readback.';
    $('review-section').hidden = confirmed;
    $('confirmed-section').hidden = !confirmed;
    $('download-receipt').href = `/api/receipt?id=${encodeURIComponent(draft.id)}`;
    $('download-receipt').download = `taulsaathi-${draft.id}.json`;
    $('evidence-list').replaceChildren();
    (draft.evidence || []).forEach((evidence) => {
      const item = document.createElement('div');
      item.className = 'evidence-item';
      const heading = document.createElement('strong');
      heading.textContent = `${labels[evidence.field] || evidence.field}: `;
      item.append(heading, document.createTextNode(`“${evidence.raw || ''}” → ${normalized(evidence.value)}`));
      $('evidence-list').append(item);
    });
    if (!(draft.evidence || []).length) {
      const note = document.createElement('p'); note.className = 'small muted'; note.textContent = 'No extraction evidence returned.'; $('evidence-list').append(note);
    }
    $('history-list').replaceChildren();
    (draft.history || []).forEach((entry) => {
      const item = document.createElement('li');
      item.textContent = `Revision ${entry.revision} · ${entry.action}: ${typeof entry.detail === 'string' ? entry.detail : JSON.stringify(entry.detail)}`;
      $('history-list').append(item);
    });
    $('original-transcript').textContent = draft.transcript || '';
    clearAudio();
    refreshControls();
  }

  function unit(text) { const node = document.createElement('small'); node.textContent = text; return node; }
  function clearAudio() {
    $('readback-audio').pause();
    $('readback-audio').removeAttribute('src');
    $('readback-audio').hidden = true;
    if (state.audioURL) URL.revokeObjectURL(state.audioURL);
    state.audioURL = null;
  }

  function setLanguage(value) {
    if (!value) return;
    if (![...$('language').options].some((option) => option.value === value)) {
      const option = document.createElement('option'); option.value = value; option.textContent = value; $('language').append(option);
    }
    $('language').value = value;
  }

  $('create-draft').addEventListener('click', () => run(async () => {
    const transcript = $('transcript').value.trim();
    const language = $('language').value;
    const originalSpeech = state.source === 'gnani' && state.transcription && state.transcription.text === transcript && state.transcription.language === language;
    const payload = { transcript, language, source: state.source === 'synthetic' ? 'synthetic' : originalSpeech ? 'gnani' : 'typed' };
    if (originalSpeech) payload.transcription_id = state.transcription.id;
    if (state.exampleId) payload.example_id = state.exampleId;
    const draft = await json('/api/draft', payload);
    renderDraft(draft);
    if (window.matchMedia('(max-width: 760px)').matches) $('record-heading').scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
  }, $('create-draft'), 'Creating draft…'));

  $('clear-input').addEventListener('click', () => {
    $('transcript').value = '';
    state.source = 'typed'; state.exampleId = null; state.transcription = null;
    document.querySelectorAll('.example-button').forEach((button) => button.classList.remove('active'));
    $('reviewed').checked = false; $('transcript-reviewed').checked = false;
    clearAudio(); sourceNote(); refreshControls(); $('transcript').focus();
  });
  function markEdited() {
    state.source = 'typed'; state.exampleId = null; state.transcription = null;
    document.querySelectorAll('.example-button').forEach((button) => button.classList.remove('active'));
    $('reviewed').checked = false; $('transcript-reviewed').checked = false;
    clearAudio(); sourceNote(); refreshControls();
  }
  $('transcript').addEventListener('input', markEdited);
  $('language').addEventListener('change', markEdited);
  $('reviewed').addEventListener('change', refreshControls);
  $('transcript-reviewed').addEventListener('change', refreshControls);
  $('warning-reason').addEventListener('input', refreshControls);
  $('resolve-warnings').addEventListener('click', () => run(async () => {
    if (hasChanges() || inputMismatch() || !$('transcript-reviewed').checked) throw new Error('Create the current draft, apply corrections and check the full transcript first.');
    const draft = await json('/api/review', { id: state.draft.id, revision: state.draft.revision, reason: $('warning-reason').value.trim() });
    renderDraft(draft);
  }, $('resolve-warnings'), 'Saving transcript review…'));
  fieldNames.forEach((field) => {
    $(`field-${field}`).addEventListener('input', () => { $('reviewed').checked = false; refreshControls(); });
    document.querySelector(`[data-apply="${field}"]`).addEventListener('click', (event) => run(async () => {
      const value = $(`field-${field}`).value.trim();
      const draft = await json('/api/revise', { id: state.draft.id, revision: state.draft.revision, field, value: value || null, reason: $('correction-reason').value.trim() || 'User corrected this field after review.' });
      renderDraft(draft);
    }, event.currentTarget, '…'));
  });

  $('confirm').addEventListener('click', () => run(async () => {
    if (!$('reviewed').checked || hasChanges() || inputMismatch()) throw new Error('Create the current draft, apply every correction and review this revision before confirming.');
    const draft = await json('/api/confirm', { id: state.draft.id, revision: state.draft.revision, reviewed: true });
    renderDraft(draft);
  }, $('confirm'), 'Confirming revision…'));

  $('readback').addEventListener('click', () => run(async () => {
    if (hasChanges() || inputMismatch()) throw new Error('Create the current draft and apply your corrections before requesting the readback.');
    const requested = { id: state.draft.id, revision: state.draft.revision };
    const response = await request('/api/readback', { method: 'POST', body: JSON.stringify(requested) });
    const blob = await response.blob();
    if (state.draft.id !== requested.id || state.draft.revision !== requested.revision) throw new Error('The record changed during voice generation. Request a fresh readback.');
    clearAudio(); state.audioURL = URL.createObjectURL(blob);
    $('readback-audio').src = state.audioURL;
    $('readback-audio').hidden = false;
    state.liveVerified = true; updateConnection();
    $('readback-note').textContent = 'Live Gnani readback returned. Check the spoken numbers against the visible record.';
    try { await $('readback-audio').play(); } catch { /* The visible native player is available when autoplay is blocked. */ }
  }, $('readback'), 'Generating voice…'));

  $('audio-file').addEventListener('change', () => {
    const file = $('audio-file').files[0];
    $('file-note').textContent = file ? `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB` : 'No recording selected.';
    $('transcription-meta').textContent = '';
    refreshControls();
  });

  function base64File(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result).split(',')[1]);
      reader.onerror = () => reject(new Error('The audio file could not be read.'));
      reader.readAsDataURL(file);
    });
  }

  $('transcribe').addEventListener('click', () => run(async () => {
    const file = $('audio-file').files[0];
    if (!file || !/\.wav$/i.test(file.name)) throw new Error('Choose a WAV audio file. Convert other recording formats to WAV first.');
    if (file.size > 8 * 1024 * 1024) throw new Error('Choose a WAV file no larger than 8 MB for this prototype.');
    const result = await json('/api/transcribe', { audio_base64: await base64File(file), language: $('language').value });
    $('transcript').value = result.transcript || '';
    state.source = 'gnani'; state.exampleId = null; state.liveVerified = true;
    state.transcription = { id: result.transcription_id, text: (result.transcript || '').trim(), language: $('language').value };
    $('reviewed').checked = false; $('transcript-reviewed').checked = false; clearAudio();
    document.querySelectorAll('.example-button').forEach((button) => button.classList.remove('active'));
    sourceNote(); updateConnection();
    $('transcription-meta').textContent = `${result.model || 'Gnani speech to text'} · ${result.elapsed_ms !== undefined ? `${formatNumber(result.elapsed_ms, 0)} ms` : 'live response'} · Review this transcript, then create a draft.`;
    if (!result.transcript) throw new Error('Gnani returned an empty transcript. Check the recording and try again.');
  }, $('transcribe'), 'Transcribing with Gnani…'));

  $('download-receipt').addEventListener('click', (event) => {
    if (state.busy || hasChanges() || inputMismatch() || !state.draft || state.draft.status !== 'confirmed') { event.preventDefault(); error('Only the current confirmed revision can be downloaded. Create a new draft for changed input, then apply and review corrections.'); }
  });
  $('print-record').addEventListener('click', () => {
    if (!state.draft || state.draft.status !== 'confirmed' || hasChanges() || inputMismatch()) { error('Create and confirm the current input before printing.'); return; }
    window.print();
  });

  async function initialize() {
    refreshControls();
    const results = await Promise.allSettled([json('/api/status'), json('/api/examples')]);
    if (results[0].status === 'fulfilled') {
      state.connected = true; state.configured = Boolean(results[0].value.gnani_configured);
      setLanguage(results[0].value.default_language);
      updateConnection();
    } else {
      $('connection-badge').textContent = 'Local server unavailable';
      $('connection-badge').className = 'connection unavailable';
      $('status-message').textContent = 'The local API could not be reached. Start the TaulSaathi server, then reload this page. No draft or live speech call has run.';
      $('status-message').className = 'status-banner warning';
    }
    $('examples').replaceChildren();
    if (results[1].status === 'fulfilled') {
      const examples = Array.isArray(results[1].value) ? results[1].value : results[1].value.examples || [];
      examples.forEach((example) => {
        const button = document.createElement('button');
        button.type = 'button'; button.className = 'example-button'; button.textContent = example.title;
        button.addEventListener('click', () => {
          $('transcript').value = example.transcript;
          state.source = 'synthetic'; state.exampleId = example.id; state.transcription = null;
          setLanguage(example.language);
          document.querySelectorAll('.example-button').forEach((item) => item.classList.toggle('active', item === button));
          $('reviewed').checked = false; $('transcript-reviewed').checked = false;
          clearAudio(); sourceNote(); refreshControls();
        });
        $('examples').append(button);
      });
      // Make the first visit useful immediately, without spending speech credits.
      // The provenance label remains synthetic and confirmation stays explicit.
      if (examples.length && !$('transcript').value.trim() && !state.draft) {
        const example = examples[0];
        $('transcript').value = example.transcript;
        state.source = 'synthetic'; state.exampleId = example.id;
        setLanguage(example.language);
        $('examples').querySelector('.example-button').classList.add('active');
        sourceNote();
        try {
          const initialDraft = await json('/api/draft', {transcript: example.transcript, language: example.language, source: 'synthetic'});
          if (!state.draft && $('transcript').value === example.transcript && $('language').value === example.language) renderDraft(initialDraft);
        } catch (err) { error(err.message || 'The sample draft could not be loaded.'); }
      }
      if (!examples.length) $('examples').textContent = 'No scenarios available. Enter a conversation below.';
    } else {
      $('examples').textContent = 'Scenarios unavailable. Enter text after starting the local server.';
    }
    refreshControls();
  }
  window.addEventListener('beforeunload', () => { if (state.audioURL) URL.revokeObjectURL(state.audioURL); });
  initialize();
})();
