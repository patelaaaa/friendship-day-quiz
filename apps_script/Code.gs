/**
 * Friendship Day Mega Quiz Event — backend
 * ------------------------------------------------
 * Deploy this bound to a Google Sheet as a Web App (Extensions > Apps Script).
 * No service account / API key needed — the Web App URL + an admin password
 * (stored as a Script Property) are the only secrets.
 *
 * Sheets used (auto-created on first call):
 *   Registrations : EntryID | Timestamp | Name | StarMakerID | TeamMember | UniqueID
 *   UniqueIDs     : UniqueID | Used | UsedBy | UsedAt
 *   Winners       : WinnerName | StarMakerID | TeamMember | DrawnAt
 *   Settings      : Key | Value
 */

const ADMIN_PASSWORD_PROP = 'ADMIN_PASSWORD';

function getSS() { return SpreadsheetApp.getActiveSpreadsheet(); }

function getSheet(name, headers) {
  const ss = getSS();
  let sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.appendRow(headers);
  }
  return sh;
}

function regSheet()  { return getSheet('Registrations', ['EntryID','Timestamp','Name','StarMakerID','TeamMember','UniqueID']); }
function idsSheet()  { return getSheet('UniqueIDs', ['UniqueID','Used','UsedBy','UsedAt']); }
function winSheet()  { return getSheet('Winners', ['WinnerName','StarMakerID','TeamMember','DrawnAt']); }
function setSheet()  { return getSheet('Settings', ['Key','Value']); }

function getSetting(key, fallback) {
  const sh = setSheet();
  const data = sh.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === key) return data[i][1];
  }
  return fallback;
}

function setSetting(key, value) {
  const sh = setSheet();
  const data = sh.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === key) { sh.getRange(i + 1, 2).setValue(value); return; }
  }
  sh.appendRow([key, value]);
}

function getAllSettings() {
  const sh = setSheet();
  const data = sh.getDataRange().getValues();
  const obj = {};
  for (let i = 1; i < data.length; i++) obj[data[i][0]] = data[i][1];
  if (obj.RegistrationClosed === undefined) obj.RegistrationClosed = 'FALSE';
  if (obj.EventDateTime === undefined) obj.EventDateTime = '2026-08-02T19:00:00+05:30';
  return obj;
}

function checkAdmin(password) {
  const stored = PropertiesService.getScriptProperties().getProperty(ADMIN_PASSWORD_PROP);
  return !!(stored && password && password === stored);
}

function jsonOut(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  try {
    const action = e.parameter.action || 'list_all';
    if (action === 'list_registrations') return jsonOut({ ok: true, data: listRegistrations() });
    if (action === 'list_winners')       return jsonOut({ ok: true, data: listWinners() });
    if (action === 'get_settings')       return jsonOut({ ok: true, data: getAllSettings() });
    if (action === 'check_admin')        return jsonOut({ ok: checkAdmin(e.parameter.password) });
    if (action === 'list_all') {
      return jsonOut({
        ok: true,
        registrations: listRegistrations(),
        winners: listWinners(),
        settings: getAllSettings()
      });
    }
    return jsonOut({ ok: false, error: 'Unknown action: ' + action });
  } catch (err) {
    return jsonOut({ ok: false, error: String(err) });
  }
}

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents || '{}');
    const action = body.action;
    if (action === 'register')       return jsonOut(registerEntry(body));
    if (action === 'toggle_closed')  return jsonOut(toggleClosed(body));
    if (action === 'delete_entry')   return jsonOut(deleteEntry(body));
    if (action === 'edit_entry')     return jsonOut(editEntry(body));
    if (action === 'record_winner')  return jsonOut(recordWinner(body));
    if (action === 'clear_winners')  return jsonOut(clearWinners(body));
    if (action === 'set_event_date') return jsonOut(setEventDate(body));
    return jsonOut({ ok: false, error: 'Unknown action: ' + action });
  } catch (err) {
    return jsonOut({ ok: false, error: String(err) });
  }
}

function listRegistrations() {
  const data = regSheet().getDataRange().getValues();
  const out = [];
  for (let i = 1; i < data.length; i++) {
    const r = data[i];
    if (!r[0]) continue;
    out.push({ entryId: r[0], timestamp: r[1], name: r[2], starmakerId: r[3], teamMember: r[4], uniqueId: r[5] });
  }
  return out;
}

function listWinners() {
  const data = winSheet().getDataRange().getValues();
  const out = [];
  for (let i = 1; i < data.length; i++) {
    const r = data[i];
    if (!r[0]) continue;
    out.push({ winnerName: r[0], starmakerId: r[1], teamMember: r[2], drawnAt: r[3] });
  }
  return out;
}

function registerEntry(body) {
  const name = String(body.name || '').trim();
  const starmakerId = String(body.starmakerId || '').trim();
  const teamMember = String(body.teamMember || '').trim();
  const uniqueId = String(body.uniqueId || '').trim().toUpperCase();

  if (String(getSetting('RegistrationClosed', 'FALSE')).toUpperCase() === 'TRUE') {
    return { ok: false, error: 'Registrations are closed. This entry cannot be submitted.' };
  }
  if (!name || !starmakerId || !teamMember || !uniqueId) {
    return { ok: false, error: 'Please complete all fields, including the unique ID.' };
  }

  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    const ids = idsSheet();
    const idData = ids.getDataRange().getValues();
    let rowIndex = -1;
    for (let i = 1; i < idData.length; i++) {
      if (String(idData[i][0]).trim().toUpperCase() === uniqueId) { rowIndex = i; break; }
    }
    if (rowIndex === -1) {
      return { ok: false, error: 'Invalid unique ID. Please enter one of the official registration IDs.' };
    }
    if (String(idData[rowIndex][1]).toUpperCase() === 'TRUE') {
      return { ok: false, error: 'This unique ID has already been used. Each unique ID can only be used once.' };
    }

    const norm = v => String(v || '').trim().toLowerCase();
    const reg = regSheet();
    const regData = reg.getDataRange().getValues();
    for (let i = 1; i < regData.length; i++) {
      const r = regData[i];
      if (norm(r[3]) === norm(starmakerId) ||
          norm(r[2]) === norm(name) || norm(r[4]) === norm(name) ||
          norm(r[2]) === norm(teamMember) || norm(r[4]) === norm(teamMember)) {
        return { ok: false, error: 'Multiple entries are not allowed. This participant or StarMaker ID is already registered.' };
      }
    }

    const entryId = 'REG-' + Date.now().toString(36).toUpperCase() + '-' + Math.random().toString(36).slice(2, 8).toUpperCase();
    reg.appendRow([entryId, new Date().toISOString(), name, starmakerId, teamMember, uniqueId]);
    ids.getRange(rowIndex + 1, 2).setValue('TRUE');
    ids.getRange(rowIndex + 1, 3).setValue(name);
    ids.getRange(rowIndex + 1, 4).setValue(new Date().toISOString());
    return { ok: true, entryId: entryId };
  } finally {
    lock.releaseLock();
  }
}

function toggleClosed(body) {
  if (!checkAdmin(body.adminPassword)) return { ok: false, error: 'Invalid admin password.' };
  setSetting('RegistrationClosed', body.closed ? 'TRUE' : 'FALSE');
  return { ok: true };
}

function setEventDate(body) {
  if (!checkAdmin(body.adminPassword)) return { ok: false, error: 'Invalid admin password.' };
  setSetting('EventDateTime', String(body.eventDateTime || ''));
  return { ok: true };
}

function deleteEntry(body) {
  if (!checkAdmin(body.adminPassword)) return { ok: false, error: 'Invalid admin password.' };
  const sh = regSheet();
  const data = sh.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === body.entryId) { sh.deleteRow(i + 1); return { ok: true }; }
  }
  return { ok: false, error: 'Entry not found.' };
}

function editEntry(body) {
  if (!checkAdmin(body.adminPassword)) return { ok: false, error: 'Invalid admin password.' };
  const sh = regSheet();
  const data = sh.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === body.entryId) {
      if (body.name !== undefined) sh.getRange(i + 1, 3).setValue(body.name);
      if (body.starmakerId !== undefined) sh.getRange(i + 1, 4).setValue(body.starmakerId);
      if (body.teamMember !== undefined) sh.getRange(i + 1, 5).setValue(body.teamMember);
      return { ok: true };
    }
  }
  return { ok: false, error: 'Entry not found.' };
}

function recordWinner(body) {
  if (!checkAdmin(body.adminPassword)) return { ok: false, error: 'Invalid admin password.' };
  winSheet().appendRow([body.winnerName || '', body.starmakerId || '', body.teamMember || '', new Date().toISOString()]);
  return { ok: true };
}

function clearWinners(body) {
  if (!checkAdmin(body.adminPassword)) return { ok: false, error: 'Invalid admin password.' };
  const sh = winSheet();
  const lastRow = sh.getLastRow();
  if (lastRow > 1) sh.deleteRows(2, lastRow - 1);
  return { ok: true };
}

/**
 * Run this ONCE manually from the Apps Script editor (select "setup" in the
 * function dropdown, click Run, approve permissions) to create the sheets
 * and seed the 70 official unique registration IDs.
 * It will NOT overwrite IDs if the UniqueIDs sheet already has data.
 */
