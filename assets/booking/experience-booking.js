
/* ELLY first-experience form. No customer email address in client code. */
(()=>{'use strict';
const endpoint='https://formspree.io/f/myeeeknl';
const schedule={1:['10:00','19:00','20:00'],2:['09:00','19:00','20:00'],3:['10:00','21:00'],4:['09:00','19:00','20:00']};
const prenatal={3:['11:00','19:00','20:00']};
const today=()=>{const d=new Date();return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-')};
const dayOf=s=>{if(!/^\d{4}-\d{2}-\d{2}$/.test(s))return -1;const [y,m,d]=s.split('-').map(Number);const date=new Date(y,m-1,d);return date.getFullYear()===y&&date.getMonth()===m-1&&date.getDate()===d?date.getDay():-1};
document.querySelectorAll('[data-elly-booking]').forEach(root=>{
 const form=root.querySelector('form'),isMom=root.dataset.ellyBooking==='momfit';
 const kind=()=>form.querySelector('input[name="lesson_type"]:checked')?.value||'';
 const date=form.querySelector('[name="preferred_date"]'),time=form.querySelector('[name="preferred_time"]');
 const dateWrap=date.closest('.eb-date-wrap');
 const syncDateHint=()=>{if(dateWrap)dateWrap.classList.toggle('eb-date-filled',!!date.value)};
 date.addEventListener('input',syncDateHint);
 date.addEventListener('change',syncDateHint);
 const groupSchedule=isMom?prenatal:schedule;
 const update=()=>{
  const group=kind().includes('3:1'),dateVal=date.value;
  time.innerHTML='<option value="">희망 시간을 선택해 주세요</option>';
  if(group){(groupSchedule[dayOf(dateVal)]||[]).forEach(t=>{const o=document.createElement('option');o.value=t;o.textContent=t;time.append(o)});time.disabled=!dateVal||time.options.length===1}
  else {time.disabled=false;for(let h=7;h<=21;h++)for(const m of ['00','30']){if(h===21&&m==='30')continue;const t=String(h).padStart(2,'0')+':'+m;const o=document.createElement('option');o.value=t;o.textContent=t;time.append(o)}}
  root.querySelector('[data-schedule-help]').textContent=group?(isMom?'산전 그룹은 수요일 11:00 · 19:00 · 20:00 중 선택할 수 있어요.':'그룹 수업 운영 요일을 선택하면 가능한 시간이 표시돼요.'):'희망 시간을 선택해 주세요. 담당자 확인 후 확정됩니다.';
 };
 date.min=today();
 form.querySelectorAll('input[name="lesson_type"]').forEach(x=>x.addEventListener('change',update));
 date.addEventListener('change',update);
 const goals=form.querySelectorAll('input[name="goals"]');
 goals.forEach(x=>x.addEventListener('change',()=>{if([...goals].filter(c=>c.checked).length>2){x.checked=false;root.querySelector('[data-goal-help]').textContent='최대 2개까지 선택할 수 있어요.'}else root.querySelector('[data-goal-help]').textContent='최대 2개 선택 가능'}));
 const stage=form.querySelector('[name="mom_stage"]'),stageWrap=root.querySelector('[data-stage-detail]'),stageLabel=root.querySelector('[data-stage-label]'),stageInput=root.querySelector('[name="stage_detail"]');
 if(stage)stage.addEventListener('change',()=>{const v=stage.value;stageWrap.hidden=v==='준비 중'||!v;stageLabel.textContent=v==='임신 중'?'현재 임신 주수 (선택)':'출산 후 경과 개월 (선택)';stageInput.value='';stageInput.placeholder=v==='임신 중'?'예: 20주':'예: 6개월'});
 const status=root.querySelector('[data-booking-status]'),submit=form.querySelector('button[type="submit"]');
 form.addEventListener('submit',async e=>{
  e.preventDefault();
  if(submit.disabled)return;
  if(!form.reportValidity())return;
  if(kind().includes('3:1')&&!((groupSchedule[dayOf(date.value)]||[]).includes(time.value))){status.textContent='선택한 날짜에는 해당 그룹 수업이 없어요. 다른 날짜를 선택해 주세요.';return}
  if(date.value<today()){status.textContent='오늘 이후 날짜를 선택해 주세요.';return}
  submit.disabled=true;status.textContent='신청 내용을 전송하고 있어요.';
  const payload=new FormData(form);
  payload.set('신청 구분',isMom?'엘리맘앤핏 산전·산후 체험':'엘리필라테스 일반 체험 및 상담');
  payload.set('희망 날짜',date.value);payload.set('희망 시간',time.value);
  payload.set('_subject',isMom?'[엘리맘앤핏] 산전·산후 체험 신청':'[엘리필라테스] 일반 체험 신청');
  try{const res=await fetch(endpoint,{method:'POST',body:payload,headers:{Accept:'application/json'}});
   if(!res.ok)throw new Error('전송 실패');
   form.reset();update();syncDateHint();if(stage&&stageWrap){stageWrap.hidden=true;if(stageInput)stageInput.value=''}status.textContent='체험 신청이 정상적으로 접수되었습니다. 담당자가 신청 내용을 확인한 후 순차적으로 연락드리겠습니다.';
  }catch(_){status.textContent='신청이 전송되지 않았어요. 잠시 후 다시 시도해 주세요.'}
  finally{submit.disabled=false}
 });
 update();syncDateHint();
});
})();
