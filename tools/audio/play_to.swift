// play_to "<device name substring>" file.wav  - plays a file on one output device without changing the Mac's default output
import AVFoundation; import CoreAudio
let args = CommandLine.arguments; let want = args[1]; let url = URL(fileURLWithPath: args[2])
var a = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDevices, mScope: kAudioObjectPropertyScopeGlobal, mElement: 0)
var sz = UInt32(0); AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject), &a, 0, nil, &sz)
var ids = [AudioObjectID](repeating: 0, count: Int(sz) / 4); AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &a, 0, nil, &sz, &ids)
var dev: AudioObjectID = 0
for id in ids { var n: Unmanaged<CFString>?; var s = UInt32(MemoryLayout<Unmanaged<CFString>?>.size)
  var na = AudioObjectPropertyAddress(mSelector: kAudioObjectPropertyName, mScope: kAudioObjectPropertyScopeGlobal, mElement: 0)
  if AudioObjectGetPropertyData(id, &na, 0, nil, &s, &n) == 0, let nm = n?.takeRetainedValue() as String?, nm.contains(want) { dev = id } }
guard dev != 0 else { print("device not found"); exit(1) }
let eng = AVAudioEngine(); let p = AVAudioPlayerNode(); eng.attach(p)
var d = dev; AudioUnitSetProperty(eng.outputNode.audioUnit!, kAudioOutputUnitProperty_CurrentDevice, kAudioUnitScope_Global, 0, &d, 4)
let f = try! AVAudioFile(forReading: url); eng.connect(p, to: eng.mainMixerNode, format: f.processingFormat)
try! eng.start(); let sem = DispatchSemaphore(value: 0)
p.scheduleFile(f, at: nil) { sem.signal() }; p.play(); sem.wait(); Thread.sleep(forTimeInterval: 0.3); print("played", url.lastPathComponent, "on device", dev)
