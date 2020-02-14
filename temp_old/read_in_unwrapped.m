%% Pre_SBAS
% This script requires a LOT of grunt work, but it provides you with
% calibrated and atmospherically-corrected scenes (at least the atmospheric
% effects due to topography)
% You will end up with a set a scenes in phase.mat
% You will end up with an unweighted stack of interferograms to get a small
% sense of the patterns in the area
% You can also generate a mask based on coherence values
%% Load all of the files you are considering
nr=2976/2; naz=960;% image size:  nr = # of x (range) pixels; 
                             % naz = # of y (azimuth) pixels
%n=79; % number of slcs 

xl = 400;
yl = 300;

% xfirst = -103.801876867;
xfirst = -104.99972534;
yfirst = 32.99972153;
% yfirst = 31.5457343603;
% xstep = 0.00069442504;
xstep = 0.00208327512;
xlast = xfirst + (xstep*(nr-1));
ylast = yfirst - (xstep*(naz-1));

X = linspace(xfirst,xlast,nr);
Y = linspace(yfirst,ylast,naz);
nr_dem = nr;
naz_dem = naz;


addpath('../duplication/interferograms/'); % Add path to where all of the 
                                           % files are                                         

unw_phase=zeros(nr,naz);
amp=zeros(nr,naz);
coh=zeros(nr,naz);

strint='20170824_20170905.i';
strunw=strrep(strint,'.i','.u');
stramp=strrep(strint,'.i','.amp');
strcc=strrep(strint,'.i','.cc'); 
% correlations
filename_c=sprintf('%s',strcc); 
fid=fopen(filename_c);
dat=fread(fid,[2*nr,inf],'float','ieee-le');
coh(:,:)=dat((nr+1):end,:);
fclose(fid);
% unwrapped phase
filename=sprintf('%s',strunw);  
fid=fopen(filename);
dat=fread(fid,[2*nr,inf],'float','ieee-le');
unw_phase(:,:)=dat(nr+1:end,:);
fclose(fid);
% % Amplitude
%     filename=sprintf('%s',stramp);  
%     fid=fopen(filename);
%     dat=fread(fid,[2*nr,inf],'float','ieee-le');
%     if subset == 1
%         temp = dat(1:2:2*nr-1,:)+dat(2:2:2*nr,:);
%         amp = amp + temp(sub_xst:sub_xst+(xl-1),sub_yst:sub_yst+(yl-1));
%     else
%         amp=amp + dat(1:2:2*nr-1,:)+dat(2:2:2*nr,:);
%     end
%     fclose(fid);
% end
% disp('Correlations read in.');
% disp('Unwrapped Phase read in.');
% amp_mean = amp./N;
% disp('Amplitude Read in.');

