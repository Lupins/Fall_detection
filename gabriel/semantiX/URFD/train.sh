dat= date '+%F_%H:%M:%S'

ep='500'
lr='0.0001'
batch='1024'
data='URFD'

python train_new.py -actions cross-train -streams temporal pose spatial ritmo saliency -class Falls NotFalls -ep $ep -lr $lr -w0 1 -mini_batch $batch -batch_norm True -fold_norm 2 -kfold video -nsplits 5 -id ${data}-train | tee ${dat}_train_${data}_all-streams_ep_${ep}_lr_${lr}_batch_${batch}.txt
