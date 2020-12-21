
## Step 1: Install Compile dependencies
```
apt install neuron neuron-dev openmpi-bin libmeschach-dev libopenmpi-dev
```
- Package: neuron
  Version: 7.6.3-1+b3
- Package: neuron-dev
  Version: 7.6.3-1+b3
- Package: openmpi-bin
  Version: 4.0.5-7
- Package: libmeschach-dev
  Version: 1.2b-14
- Package: libopenmpi-dev
  Version: 4.0.5-7
## Step 2: Compile
```
cd SchreglmannEtAl2020/CCTC_model/modfiles
nrnivmodl
mv x86_64 ../
```
## Step 3: Ensure directories exist
```
cd ../
mkdir -p recordings_full
mkdir -p temporary
```
## Step 4: Install model execution dependencies
```
apt install octave python3-neuron octave-signal
```
Installed 
- Package: octave
  Version: 6.1.0-2
- Package: python3-neuron
  Version: 7.6.3-1+b3
## Step 5: Execute model
Comment out the call to `rng` which sets a random seed and which is not
currently supported in octave.

Then run octave like this:
```
octave run__phase_locked_tACS.m
```
and then like this
```
octave run_non_phase_locked_tACS.m
```
Warnings may be output like this:
```
exp(inf) out of range, returning exp(700)
exp(inf) out of range, returning exp(700)
exp(inf) out of range, returning exp(700)
exp(inf) out of range, returning exp(700)
```
Took ~32 minutes on my laptop with "Intel(R) Core(TM) i7-8550U CPU @ 1.80GHz"

