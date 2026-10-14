"""Decode real encoder output with Pillow (independent of the JS implementation).

Requires Node.js on PATH and Pillow. Runs entirely in memory, with no browser.
"""
import base64
import io
import json
from pathlib import Path
import subprocess
import unittest

from PIL import Image


class GifRoundTrip(unittest.TestCase):
    def test_growth_frames_transparency_timing_and_lzw_dictionary_resets(self):
        script = r"""
const X=require('./barrier_export.js'), E=require('./gif_encoder.js');
(async()=>{
  const W=257,H=193,N=12, frames=X.timeline(6,N,6,6);
  // A deterministic, low-palette but hard-to-compress field exercises LZW's
  // dictionary growth/reset. Then a growing colored area tests delta frames,
  // unchanged pixels, and a completely unchanged final frame.
  let seed=11; const background=new Uint8Array(W*H);
  for(let i=0;i<background.length;i++){seed=(Math.imul(seed,1664525)+1013904223)>>>0;background[i]=seed>>>30;}
  const colors=[[255,255,255],[0,0,0],[240,0,0],[0,0,240],[0,240,0]];
  function rgba(frame){
    const k=Math.min(frame,N-2), data=new Uint8Array(W*H*4);
    for(let y=0;y<H;y++)for(let x=0;x<W;x++){
      const i=y*W+x, color=colors[x<k*20 && y>20 && y<150?4:background[i]];
      data.set(color,i*4);data[i*4+3]=255;
    }
    return data;
  }
  const blob=await X.encode({encoder:E,width:W,height:H,frames,cancelled:()=>false,
    render:rgba,progress:()=>{},yieldFrame:async()=>{}});
  console.log(JSON.stringify({gif:Buffer.from(await blob.arrayBuffer()).toString('base64'),
    expected:Array.from({length:N},(_,k)=>Buffer.from(rgba(k)).toString('base64')),
    delays:frames.map(f=>f.delay*10),width:W,height:H}));
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
        data = json.loads(subprocess.check_output(
            ["node", "-e", script], cwd=Path(__file__).parent, text=True))
        image = Image.open(io.BytesIO(base64.b64decode(data["gif"])))
        self.assertEqual(image.size, (data["width"], data["height"]))
        self.assertEqual(image.n_frames, len(data["expected"]))
        self.assertEqual(image.info["loop"], 0)
        for frame, expected in enumerate(data["expected"]):
            image.seek(frame)
            self.assertEqual(image.info["duration"], data["delays"][frame])
            self.assertEqual(image.convert("RGBA").tobytes(), base64.b64decode(expected))
        self.assertEqual(sum(data["delays"]), 7000)


if __name__ == "__main__":
    unittest.main()
