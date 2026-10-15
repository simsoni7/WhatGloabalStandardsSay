import {ApiError,hash} from './core';

// Split only the model's PNG input. Stored reference bytes remain immutable.
// Reconstruct one scanline at a time; never allocate a full decoded screenshot.
const MAX_IMAGE_BYTES=3.75*1024*1024,MAX_RAW_TILE=12*1024*1024;
const SIGNATURE=Uint8Array.from([137,80,78,71,13,10,26,10]);
const crcTable=Uint32Array.from({length:256},(_,n)=>{let c=n;for(let k=0;k<8;k++)c=c&1?0xedb88320^(c>>>1):c>>>1;return c>>>0;});
function chunk(type:string,data:Uint8Array){const out=new Uint8Array(data.length+12),view=new DataView(out.buffer);view.setUint32(0,data.length);out.set(new TextEncoder().encode(type),4);out.set(data,8);let crc=0xffffffff;for(let i=4;i<8+data.length;i++)crc=crcTable[(crc^out[i])&255]^(crc>>>8);view.setUint32(8+data.length,(crc^0xffffffff)>>>0);return out;}
function join(parts:Uint8Array[]){const out=new Uint8Array(parts.reduce((n,p)=>n+p.length,0));let offset=0;for(const p of parts){out.set(p,offset);offset+=p.length;}return out;}
function paeth(a:number,b:number,c:number){const p=a+b-c,pa=Math.abs(p-a),pb=Math.abs(p-b),pc=Math.abs(p-c);return pa<=pb&&pa<=pc?a:pb<=pc?b:c;}
export type VisionTile={bytes:Uint8Array,mime:string,width:number,height:number,startRow:number,endRow:number,sha256:string,derived:boolean};
export async function splitPngForVision(bytes:Uint8Array,maxTiles=20,maxOutputBytes=12*1024*1024):Promise<VisionTile[]>{
 const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);if(bytes.length<45||!SIGNATURE.every((n,i)=>bytes[i]===n))throw new ApiError(409,'invalid_image','PNG 사진을 읽지 못했습니다.');
 const width=view.getUint32(16),height=view.getUint32(20),depth=bytes[24],color=bytes[25],channels:Record<number,number>={0:1,2:3,3:1,4:2,6:4};
 if(!width||!height||width>8000||height>16000||width*height>64000000||!channels[color]||![1,2,4,8,16].includes(depth)||bytes[26]!==0||bytes[27]!==0||bytes[28]!==0)throw new ApiError(413,'vision_image_limit','이 PNG 형식은 자동 분할할 수 없습니다. AI 분석용으로 한 변 8,000픽셀 이하 사진을 사용해 주세요.');
 const rowBytes=Math.ceil(width*channels[color]*depth/8),bpp=Math.max(1,Math.ceil(channels[color]*depth/8)),rowLength=rowBytes+1,tileHeight=Math.min(6000,Math.floor(MAX_RAW_TILE/rowLength));
 if(Math.ceil(height/tileHeight)>maxTiles)throw new ApiError(413,'vision_tile_limit','긴 화면 사진이 많아 한 번에 분석할 수 없습니다. 나누어 제안해 주세요.');
 // ICC/EXIF and other optional payloads are omitted from AI-only derivatives.
 const ihdr=new Uint8Array(bytes.subarray(16,29)),idats:Uint8Array[]=[],metadata:Uint8Array[]=[];
 let offset=8;while(offset+12<=bytes.length){const length=view.getUint32(offset),end=offset+12+length;if(end>bytes.length)throw new ApiError(409,'invalid_image','PNG 사진을 읽지 못했습니다.');const type=new TextDecoder().decode(bytes.subarray(offset+4,offset+8));let sourceCrc=0xffffffff;for(let i=offset+4;i<offset+8+length;i++)sourceCrc=crcTable[(sourceCrc^bytes[i])&255]^(sourceCrc>>>8);if(((sourceCrc^0xffffffff)>>>0)!==view.getUint32(offset+8+length))throw new ApiError(409,'invalid_image','PNG 사진의 무결성 검사를 통과하지 못했습니다.');if(type==='IDAT')idats.push(bytes.subarray(offset+8,offset+8+length));else if((type==='PLTE'&&length>0&&length<=768&&length%3===0)||(type==='tRNS'&&length<=256)||(type==='sRGB'&&length===1)||(type==='gAMA'&&length===4)||(type==='cHRM'&&length===32))metadata.push(bytes.slice(offset,end));else if(type==='PLTE'||type==='tRNS')throw new ApiError(409,'invalid_image','PNG 색상 정보를 읽지 못했습니다.');offset=end;}
 if(!idats.length)throw new ApiError(409,'invalid_image','PNG 사진 내용이 없습니다.');
 const reader=new Blob(idats as BlobPart[]).stream().pipeThrough(new DecompressionStream('deflate')).getReader();let pending:Uint8Array=new Uint8Array(),pendingOffset=0,previous=new Uint8Array(rowBytes),tile=new Uint8Array(rowLength*Math.min(tileHeight,height)),tileRows=0,startRow=0;const tiles:VisionTile[]=[];let outputBytes=0;
 async function emit(raw:Uint8Array,rows:number,start:number):Promise<void>{
  const compressed=new Uint8Array(await new Response(new Blob([raw as BlobPart]).stream().pipeThrough(new CompressionStream('deflate'))).arrayBuffer());
  const header=ihdr.slice();new DataView(header.buffer).setUint32(4,rows);const encoded=join([SIGNATURE,chunk('IHDR',header),...metadata,chunk('IDAT',compressed),chunk('IEND',new Uint8Array())]);
  if(encoded.length>MAX_IMAGE_BYTES){if(rows<2)throw new ApiError(413,'vision_image_limit','사진 한 줄의 용량이 너무 커 분석할 수 없습니다.');const half=Math.floor(rows/2);await emit(raw.subarray(0,half*rowLength),half,start);await emit(raw.subarray(half*rowLength),rows-half,start+half);return;}
  if(tiles.length>=maxTiles)throw new ApiError(413,'vision_tile_limit','긴 화면 사진이 많아 한 번에 분석할 수 없습니다. 나누어 제안해 주세요.');
  outputBytes+=encoded.length;if(outputBytes>maxOutputBytes)throw new ApiError(413,'analysis_size_limit','AI 분석용 사진의 합계 용량이 커서 나누어 제안해야 합니다. 원본 사진은 그대로 보관되어 있습니다.');
  tiles.push({bytes:encoded,mime:'image/png',width,height:rows,startRow:start,endRow:start+rows,sha256:await hash(encoded),derived:true});
 }
 try{for(let y=0;y<height;y++){
   const encodedRow=new Uint8Array(rowLength);let filled=0;while(filled<rowLength){if(pendingOffset===pending.length){const next=await reader.read();if(next.done)throw new ApiError(409,'invalid_image','PNG 사진 내용이 끝까지 읽히지 않습니다.');pending=next.value;pendingOffset=0;}const take=Math.min(rowLength-filled,pending.length-pendingOffset);encodedRow.set(pending.subarray(pendingOffset,pendingOffset+take),filled);pendingOffset+=take;filled+=take;}
   const filter=encodedRow[0];if(filter>4)throw new ApiError(409,'invalid_image','PNG 압축 형식을 읽지 못했습니다.');const current=encodedRow.subarray(1);
   for(let x=0;x<rowBytes;x++){const left=x>=bpp?current[x-bpp]:0,up=previous[x],upperLeft=x>=bpp?previous[x-bpp]:0;current[x]=(current[x]+(filter===1?left:filter===2?up:filter===3?Math.floor((left+up)/2):filter===4?paeth(left,up,upperLeft):0))&255;}
   // Filter zero makes every output tile independent of the preceding tile.
   tile.set(current,tileRows*rowLength+1);previous=current;tileRows++;
   if(tileRows===tileHeight||y===height-1){await emit(tile,tileRows,startRow);startRow=y+1;tileRows=0;if(y<height-1)tile=new Uint8Array(rowLength*Math.min(tileHeight,height-y-1));}
  }
  if(pendingOffset!==pending.length||!(await reader.read()).done)throw new ApiError(409,'invalid_image','PNG 사진의 크기와 압축 내용이 일치하지 않습니다.');
  return tiles;
 }finally{await reader.cancel().catch(()=>{});}
}
