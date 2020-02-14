% SBAS with no model assumed
% STEP1: read in coherence/amplitude/phase(unwrapped) files
% STEP2: inversion: Bv=deltaphi
% STEP3: save velocity file for later analysis

clear ; clc; close all;

%% %%%%%%%%%%%%%%%%%%% PREPARATION %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% First specify Data Directory
datadir='/data2/yjzheng/SBAS_new_CValley/city_100_800';

% Then specify some parameters (can be found in the singlelook table in the database file)
nr=728;naz=882; % image size
nslc=37; % number of acquisitions
flatlistdir=sprintf('%s/flatlist',datadir);
sbaslist=importdata(flatlistdir);
mpair=length(sbaslist); % number of SB pairs
lamda=0.03; % wavelength, in meters
ifderamp=0; % if need to remove orbital ramp, set to 1.
iflag=1; % use deramped phase. otherwise, set to 0.

tlist=sprintf('%s/sbaslist',datadir);
timelist=importdata(tlist);

%% %%%%%%%%%%%%%%%%%%% OPTIONAL: DERAMP %%%%%%%%%%%%%%%%%%%%%%%%%%%%
if ifderamp==1
    u_deramp=orbit_ramp_rm_yj(nr,naz,datadir);
    display('deramp completed')
end

%% %%%%%%%%%%%%%%%%%%% STEP 1 %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% allocate memory for amp,coh,phase files
phase=zeros(naz,nr,mpair);
amp=zeros(naz,nr);
amp2=amp';
coh=zeros(naz,nr,mpair);

% load corresponding files
for i=1:mpair
    strint=sbaslist{i};
    if iflag==0
        strunw=strrep(strint,'.flat','.u');
    else
        strunw=strrep(strint,'.flat','.u_deramp');
    end
    stramp=strrep(strint,'.flat','.amp');
    strcc=strrep(strint,'.flat','.cc'); 
% coherence files
    filename_c=sprintf('%s/%s',datadir,strcc); 
    fid=fopen(filename_c);
    dat=fread(fid,[2*nr,inf],'float','ieee-le');
    coh(:,:,i)=dat((nr+1):end,:)';
    fclose(fid);
% unwrapped igrams    
    filename=sprintf('%s/%s',datadir,strunw);  
    fid=fopen(filename);
    dat=fread(fid,[2*nr,inf],'float','ieee-le');
    phase(:,:,i)=dat(nr+1:end,:)';
    amp2=amp2+dat(1:nr,:);
    fclose(fid);
% amplitudes    
    filename=sprintf('%s/%s',datadir,stramp);  
    fid=fopen(filename);
    dat=fread(fid,[2*nr,inf],'float','ieee-le');
    amp=amp+dat(1:2:2*nr-1,:)'+dat(2:2:2*nr,:)';
    fclose(fid); 
end
amp=amp./mpair;
display('Files loaded.')

indx=coh(:)>1;
coh(indx)=1;
indx=coh(:)<0;
coh(indx)=0;
coh_mean=mean(coh,3);
indx=coh_mean(:)>0.1;
mask=nan(nr,naz)';
mask(indx)=1;
amp=amp.*mask;

% save dat mask phase coh amp nr naz nslc mpair;

%% %%%%%%%%%%%%%%%%%%%%%%%%%%%%% STEP 2 %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% load B matrix generated from sbas_setup.py
Bdir=sprintf('%s/Tm.out',datadir);
load (Bdir)
% determine a reference pixel (assumed no deformation)
r_ref=407;
az_ref=307;
refphase=mean(mean(phase(az_ref,r_ref,:),1),2);
% least squares inversion
velocity=zeros(naz,nr,nslc-1);
Tminv=pinv(Tm);
display('inversion starts:')
for jj=1:naz
    if mod(jj,50)==0
        disp(jj);
    end
    for ii=1:nr
        
        % check coherence file, determine if we still want to calculate
        % this point.
        cohi=coh(jj,ii,:);
        cohi=cohi(:);
        index=find(cohi(:)>0.1);
        Neff=length(index);
        if Neff<10
            velocity(jj,ii,:)=NaN;
        else
            w=cohi/max(cohi);
            W=diag(w);
            Tmw=sqrt(W)*Tm;
            d=phase(jj,ii,:)-refphase;
            d=sqrt(W)*d(:);
            velocity(jj,ii,:)=pinv(Tmw)*d;
        end
    end
end

% load timedel.out to include in the solution package
dtk=load(sprintf('%s/timedeltas.out',datadir));
save velocity_solution velocity phase refphase amp dtk nslc mpair nr naz lamda 


% compute and save average phase
amp2=amp2./mpair;
avgphase=zeros(nr*2,naz);
avgphase(1:nr,:)=amp2;
temp=(sum(phase,3)-sum(refphase,3))/mpair;
avgphase(nr+1:end,:)=temp';
avephase='averagephase';

outfile=sprintf('%s/%s',datadir,avephase);
fid=fopen(outfile,'w');
fwrite(fid,avgphase,'float');
fclose(fid);
