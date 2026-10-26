globalThis.fsExtract=await import("node:fs/promises");
globalThis.extractPaths={"json":"E:/Git hub/mangpai-fusion/tiekoulu_1507_to_1428.json","md":"E:/Git hub/mangpai-fusion/tiekoulu_1507_to_1428.md"};
globalThis.parseCaseText=function(doc,period,birth){
 const clean=doc.replace(/\uFFFC/g,"").replace(/\u00A0/g," ");
 const titleLine=clean.split("\n").map(s=>s.trim()).find(s=>s.includes("铁口箓")&&new RegExp(`(?:第)?${period}期`).test(s));
 if(!titleLine)throw new Error("Current detail title does not match "+period);
 const detail=clean.slice(clean.indexOf(titleLine)).split("全部评论")[0];
 const shownCount=Number(detail.match(/题数[：:]\s*(\d+)/)?.[1]);
 const chunks=[...detail.matchAll(/(?:^|\n)(\d+)\.[ \t]*(\[(?:单选|多选)题\])([\s\S]*?)(?=\n\d+\.[ \t]*\[(?:单选|多选)题\]|$)/g)];
 const questions=chunks.map(m=>{
   const beforeAnswer=m[3].split(/\n答案\s*\n/)[0];
   const beforeOpts=beforeAnswer.split(/\n[A-Z][:：]/)[0].replace(/\n\s*\d+分\s*$/,"").trim().replace(/\s*\n\s*/g,"");
   const options={};for(const o of beforeAnswer.matchAll(/(?:^|\n)([A-Z])[:：]\s*([\s\S]*?)(?=\n[A-Z][:：]|$)/g))options[o[1]]=o[2].trim().replace(/\s*\n\s*/g,"");
   const ansBlock=m[3].split(/正确答案[:：]/)[1];if(ansBlock==null)throw new Error("Missing answer");
   const answers=ansBlock.split("\n").map(s=>s.trim()).filter(s=>/^[A-Z](?:[,，、 ]+[A-Z])*$/.test(s)).flatMap(s=>s.match(/[A-Z]/g));
   if(!answers.length)throw new Error("Empty answer");
   const q={q_index:Number(m[1]),question:m[2]+beforeOpts,options,correct_answer:answers.join(",")};
   if(!q.question||Object.keys(options).length<2||Object.values(options).some(v=>!v)||answers.some(a=>!options[a])||(m[2]==="[单选题]"&&answers.length!==1))throw new Error("Invalid question "+q.q_index);
   return q;
 });
 if(!shownCount||questions.length!==shownCount||questions.some((q,i)=>q.q_index!==i+1))throw new Error("Question count/index mismatch "+questions.length+"/"+shownCount);
 return {period:`第${period}期`,title:titleLine,birth_info:{line1_solar:birth[0],line2_lunar:birth[1],line3_true_solar:birth[2],full_chart_text:"按要求未读取命盘图片。"},questions};
};
globalThis.renderCase=function(c){return `## ${c.period}\n\n标题：${c.title}\n\n### 出生信息\n\n- ${c.birth_info.line1_solar}\n- ${c.birth_info.line2_lunar}\n- ${c.birth_info.line3_true_solar}\n- 完整命盘：${c.birth_info.full_chart_text}\n\n### 选择题\n\n`+c.questions.map(q=>`${q.q_index}. **${q.question}**\n`+Object.entries(q.options).map(([k,v])=>`   - ${k}. ${v}`).join("\n")+`\n   - 正确答案：${q.correct_answer}\n`).join("\n");};
globalThis.checkSaved=function(arr,md){const nums=arr.map(c=>Number(c.period.match(/\d+/)[0]));const mnums=[...md.matchAll(/^## 第(\d+)期\s*$/gm)].map(m=>Number(m[1]));if(new Set(nums).size!==nums.length||nums.some((n,i)=>i&&n!==nums[i-1]-1)||JSON.stringify(nums)!==JSON.stringify(mnums))throw new Error("Saved period continuity/JSON-Markdown mismatch");return {count:nums.length,first:nums[0],last:nums.at(-1),next:nums.at(-1)-1};};
globalThis.saveCase=async function(c){
 const oldJson=await fsExtract.readFile(extractPaths.json,"utf8");const old=JSON.parse(oldJson);const md=await fsExtract.readFile(extractPaths.md,"utf8");checkSaved(old,md);
 const n=Number(c.period.match(/\d+/)[0]);if(n!==Number(old.at(-1).period.match(/\d+/)[0])-1||old.some(x=>x.period===c.period))throw new Error("Unexpected new period");
 if(!c.birth_info.line1_solar||!c.birth_info.line2_lunar||!c.birth_info.line3_true_solar||c.questions.some((q,i)=>q.q_index!==i+1||!q.question||!Object.keys(q.options).length||q.correct_answer.split(",").some(a=>!q.options[a])))throw new Error("Incomplete new case");
 const added=renderCase(c);const newJson=oldJson.replace(/\s*\]\s*$/,",\n"+JSON.stringify(c,null,2).split("\n").map(l=>"  "+l).join("\n")+"\n]\n");
 await fsExtract.writeFile(extractPaths.json,newJson,"utf8");
 try{await fsExtract.appendFile(extractPaths.md,"\n"+added,"utf8");}catch(e){await fsExtract.writeFile(extractPaths.json,oldJson,"utf8");throw e;}
 const reread=JSON.parse(await fsExtract.readFile(extractPaths.json,"utf8"));const rereadMd=await fsExtract.readFile(extractPaths.md,"utf8");
 const checked=checkSaved(reread,rereadMd);
 if(JSON.stringify(reread.slice(0,-1))!==JSON.stringify(old)||JSON.stringify(reread.at(-1))!==JSON.stringify(c)||!rereadMd.startsWith(md)||!rereadMd.endsWith(added))throw new Error("Saved case content mismatch");
 globalThis.savedCases=reread;globalThis.savedMd=rereadMd;nodeRepl.write(JSON.stringify({...checked,qCount:c.questions.length,answers:c.questions.map(q=>q.correct_answer)}));
};
globalThis.capture=async function(text=false){globalThis.state=await sky.get_window_state({window:targetWindow,include_screenshot:true,include_text:text});targetWindow=state.window;if(text){const doc=state.accessibility?.document_text??"";if(!doc.includes("正确答案")){nodeRepl.write("Detail text not stable yet; reobserve.");return;}const titles=doc.split("\n").filter(s=>s.includes("铁口箓")&&/\d+期/.test(s));if(titles.length!==1){nodeRepl.write("Mixed or stale page text; reobserve.");return;}const p=Number(titles[0].match(/(\d+)期/)[1]);const parsed=parseCaseText(doc,p,["","",""]);globalThis.observedParsed=parsed;nodeRepl.write(JSON.stringify({title:parsed.title,count:parsed.questions.length,questions:parsed.questions},null,2));}};
globalThis.clickObserved=async function(x,y,text=false,delay=700){const ob=state;if(!ob?.screenshots?.[0]?.id)throw new Error("Need screenshot observation");state=null;await sky.click({window:ob.window,screenshotId:ob.screenshots[0].id,x,y});await new Promise(r=>setTimeout(r,delay));await capture(text);};
globalThis.keyBatch=async function(key,n,text=false,pauseEvery=0,pauseMs=0){const ob=state;if(!ob)throw new Error("Need observation");state=null;const t=Date.now();for(let i=0;i<n;i++){await sky.press_key({window:ob.window,key});if(pauseEvery&&(i+1)%pauseEvery===0)await new Promise(r=>setTimeout(r,pauseMs));}await new Promise(r=>setTimeout(r,500));await capture(text);nodeRepl.write(JSON.stringify({key,n,pauseEvery,pauseMs,elapsedMs:Date.now()-t}));};