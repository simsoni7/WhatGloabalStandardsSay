// Validate container signatures and bounded dimensions without decoding or extracting text.
export function imageMime(bytes: Uint8Array): string | null {
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),word=(start:number,len:number)=>new TextDecoder().decode(bytes.subarray(start,start+len));
  const dimensions=(width:number,height:number)=>width>0&&height>0&&width<=16000&&height<=16000&&width*height<=64000000;
  if(bytes.length>=45 && [137,80,78,71,13,10,26,10].every((n,i)=>bytes[i]===n)) {
    if(view.getUint32(8)!==13||word(12,4)!=='IHDR'||!dimensions(view.getUint32(16),view.getUint32(20)))return null;
    let offset=8,ended=false; while(offset+12<=bytes.length){const length=view.getUint32(offset); if(length>bytes.length-offset-12)return null;const type=word(offset+4,4);offset+=length+12;if(type==='IEND'){ended=length===0&&offset===bytes.length;break;}} return ended?'image/png':null;
  }
  if(bytes.length>20&&bytes[0]===255&&bytes[1]===216&&bytes[bytes.length-2]===255&&bytes[bytes.length-1]===217){
    let offset=2;while(offset+3<bytes.length){if(bytes[offset++]!==255)return null;while(bytes[offset]===255)offset++;const marker=bytes[offset++];if(marker===218)break;if(marker===1||(marker>=208&&marker<=215))continue;const length=view.getUint16(offset);if(length<2||offset+length>bytes.length)return null;if([192,193,194,195,197,198,199,201,202,203,205,206,207].includes(marker)){if(length<8)return null;return dimensions(view.getUint16(offset+5),view.getUint16(offset+3))?'image/jpeg':null;}offset+=length;}return null;
  }
  if(bytes.length>=30&&word(0,4)==='RIFF'&&word(8,4)==='WEBP'&&view.getUint32(4,true)+8===bytes.length){const type=word(12,4);if(type==='VP8X'){const width=1+bytes[24]+(bytes[25]<<8)+(bytes[26]<<16),height=1+bytes[27]+(bytes[28]<<8)+(bytes[29]<<16);return dimensions(width,height)?'image/webp':null;}if(type==='VP8 '&&bytes[23]===157&&bytes[24]===1&&bytes[25]===42)return dimensions(view.getUint16(26,true)&16383,view.getUint16(28,true)&16383)?'image/webp':null;if(type==='VP8L'&&bytes[20]===47){const bits=view.getUint32(21,true);return dimensions((bits&16383)+1,((bits>>>14)&16383)+1)?'image/webp':null;}}return null;
}
