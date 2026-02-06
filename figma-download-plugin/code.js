/**
 * UGC 图片导出下载 - Figma 插件
 * 支持：输出路径、下载后关闭面板、可选压缩服务（POST 图片得压缩图，保存为 原名_compress.ext）
 */
const SUPPORTED_FORMATS = ['PNG', 'JPG'];
const DEFAULT_SCALE = 3;
const DEFAULT_FORMAT = 'PNG';
/** 默认压缩服务地址，与同目录下 compress-service-url.txt 内容一致，首次打开会预填 */
const DEFAULT_COMPRESS_SERVICE_URL = 'http://localhost:8765/compress';

const uiHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
*{box-sizing:border-box}
body{margin:0;padding:12px 16px;font-family:Inter,-apple-system,sans-serif;font-size:12px;color:#333}
h3{margin:0 0 12px 0;font-size:14px;font-weight:600}
.row{margin-bottom:12px}
label{display:block;margin-bottom:4px;font-weight:500;color:#666}
select,input{width:100%;padding:8px 10px;border:1px solid #e0e0e0;border-radius:6px;font-size:12px;background:#fff}
select:focus,input:focus{outline:none;border-color:#0d99ff}
button{width:100%;margin-top:8px;padding:10px 16px;font-size:13px;font-weight:500;color:#fff;background:#0d99ff;border:none;border-radius:6px;cursor:pointer}
button:hover{background:#0b85e0}
.hint{margin-top:6px;font-size:11px;color:#888;line-height:1.4}
#status{margin-top:10px;padding:8px 10px;border-radius:6px;font-size:11px;min-height:20px}
#status.error{background:#ffebee;color:#c62828}
#status.success{background:#e8f5e9;color:#2e7d32}
</style>
</head>
<body>
<h3>UGC 图片导出</h3>
<!-- 暂不需要：输出路径
<div class="row"><label>输出路径（保存时的子目录，如 figma_export 或 assets/images）</label>
<input type="text" id="outputPath" placeholder="留空则保存到浏览器默认下载目录" />
</div>
-->
<div class="row"><label>倍率</label>
<select id="scale"><option value="1">1x</option><option value="2">2x</option><option value="3" selected>3x</option><option value="4">4x</option></select>
</div>
<div class="row"><label>格式</label>
<select id="format"><option value="PNG" selected>PNG</option><option value="JPG">JPG</option></select>
</div>
<div class="row"><label>压缩服务 URL（可选，会记住）</label>
<input type="text" id="compressScript" placeholder="http://localhost:8765/compress" />
<p class="hint">本机先运行: python scripts/figma_compress_server.py。填一次即可，下次自动带出。</p>
</div>
<div class="row">
<label style="display:flex;align-items:center;gap:8px;cursor:pointer"><input type="checkbox" id="onlyCompressed" /> 仅下载压缩图（不下载原图，适合多张 3x+TinyPNG 一步到位）</label>
</div>
<button id="btn">下载选中图层（多选即多张）</button>
<div id="status"></div>
<script>
(function(){
var outputPath=document.getElementById('outputPath'),scale=document.getElementById('scale'),format=document.getElementById('format'),compressScript=document.getElementById('compressScript'),btn=document.getElementById('btn'),status=document.getElementById('status');
function setStatus(t,k){ status.textContent=t||''; status.className=k||''; }
function downloadBlob(bytes,name,mime){
  var blob=new Blob([bytes],{type:mime}), url=URL.createObjectURL(blob), a=document.createElement('a');
  a.href=url;a.download=name;a.click();URL.revokeObjectURL(url);
}
window.onmessage=function(ev){
  var m=ev.data&&ev.data.pluginMessage; if(!m) return;
  if(m.type==='init'){ if(m.compressServiceUrl!=null) compressScript.value=m.compressServiceUrl; return; }
  if(m.type==='export'){
    var raw=m.bytes, bytes=raw instanceof Uint8Array ? raw : new Uint8Array(raw||[]), name=m.name||'export.png', isPng=/\\.png$/i.test(name), mime=isPng?'image/png':'image/jpeg';
    downloadBlob(bytes,name,mime);
  }else if(m.type==='done'){ setStatus('已触发下载，请在弹出的窗口中选择保存位置；若未弹窗请到默认下载目录查看。用完后可手动关闭此面板。','success'); }
  else if(m.type==='error'){ setStatus(m.message||'出错','error'); }
};
parent.postMessage({pluginMessage:{type:'getConfig'}},'*');
btn.onclick=function(){
  setStatus('');
  var out=outputPath&&outputPath.value ? String(outputPath.value).trim() : '';
  var url=compressScript&&compressScript.value ? String(compressScript.value).trim() : '';
  var onlyComp=!!(document.getElementById('onlyCompressed')&&document.getElementById('onlyCompressed').checked);
  parent.postMessage({pluginMessage:{type:'download',outputPath:out||undefined,compressServiceUrl:url||undefined,onlyCompressed:onlyComp,scale:parseInt(scale.value,10)||3,format:format.value}},'*');
};
})();
</script></body></html>`;

figma.showUI(uiHtml, { width: 400, height: 420 });

async function compressViaService(bytes, serviceUrl) {
  const url = String(serviceUrl).trim();
  if (!url) return null;
  const r = await fetch(url, { method: 'POST', body: bytes });
  if (!r.ok) throw new Error('压缩服务返回 ' + r.status);
  const buf = await r.arrayBuffer();
  return new Uint8Array(buf);
}

figma.ui.onmessage = async (msg) => {
  if (msg.type === 'getConfig') {
    const url = await figma.clientStorage.getAsync('compressServiceUrl');
    figma.ui.postMessage({ type: 'init', compressServiceUrl: url != null && url !== '' ? url : DEFAULT_COMPRESS_SERVICE_URL });
    return;
  }

  if (msg.type !== 'download') return;
  const { scale = DEFAULT_SCALE, format = DEFAULT_FORMAT, outputPath, compressServiceUrl, onlyCompressed } = msg;
  const selection = figma.currentPage.selection.slice();

  if (selection.length === 0) {
    figma.ui.postMessage({ type: 'error', message: '请先选中要导出的图层或帧' });
    return;
  }

  const exportFormat = String(format).toUpperCase();
  if (!SUPPORTED_FORMATS.includes(exportFormat)) {
    figma.ui.postMessage({ type: 'error', message: '暂不支持格式: ' + format + '，请用 PNG 或 JPG' });
    return;
  }

  const scaleNum = Math.max(1, Math.min(4, parseInt(scale, 10) || DEFAULT_SCALE));
  const outPrefix = outputPath && String(outputPath).trim() ? String(outputPath).trim().replace(/\/+$/, '') : '';
  const compressUrl = compressServiceUrl && String(compressServiceUrl).trim() ? String(compressServiceUrl).trim() : '';
  if (compressUrl) {
    await figma.clientStorage.setAsync('compressServiceUrl', compressUrl);
  }
  const onlyComp = !!onlyCompressed && !!compressUrl;

  try {
    for (let i = 0; i < selection.length; i++) {
      const node = selection[i];
      if (!('exportAsync' in node)) {
        figma.ui.postMessage({ type: 'error', message: '「' + node.name + '」不支持导出为图片' });
        continue;
      }
      const bytes = await node.exportAsync({
        format: exportFormat,
        constraint: { type: 'SCALE', value: scaleNum },
      });
      const safeId = node.id.replace(/:/g, '_');
      const ext = exportFormat.toLowerCase() === 'jpg' ? 'jpg' : 'png';
      const baseName = safeId + '@' + scaleNum + 'x.' + ext;
      const fullName = outPrefix ? outPrefix + '/' + baseName : baseName;

      if (!onlyComp) {
        figma.ui.postMessage({ type: 'export', bytes: bytes, name: fullName });
      }

      if (compressUrl) {
        try {
          const compressed = await compressViaService(bytes, compressUrl);
          if (compressed && compressed.length > 0) {
            const compressName = onlyComp
              ? (outPrefix ? outPrefix + '/' + baseName : baseName)
              : (outPrefix ? outPrefix + '/' + safeId + '@' + scaleNum + 'x_compress.' + ext : safeId + '@' + scaleNum + 'x_compress.' + ext);
            figma.ui.postMessage({ type: 'export', bytes: compressed, name: compressName });
          }
        } catch (e) {
          if (onlyComp) {
            figma.ui.postMessage({ type: 'error', message: '压缩失败: ' + (e && e.message ? e.message : String(e)) });
          } else {
            figma.ui.postMessage({ type: 'error', message: '压缩失败（已下原图）: ' + (e && e.message ? e.message : String(e)) });
          }
        }
      }
    }
    figma.ui.postMessage({ type: 'done' });
  } catch (e) {
    figma.ui.postMessage({ type: 'error', message: '导出失败: ' + (e && e.message ? e.message : String(e)) });
  }
};
