# Linux-Cluster
Linux cluster using ansible for orchestration and freeipa for idM
ansible all -m ping --ask-vault-pass VERIFY HOSTS
ansible-playbook playbooks/site.yml --ask-vault-pass effectuate the orchestration
# kickstart FreeIPA centralized idM
ssh into the controller host, run kinit admin to get Kerberos admin ticket. Then add a new user through ipa and group-add-member to the cluster operators group. you should be able to ssh into other hosts with that same user by now,  flip the enforce_hbac variable from false to true and now the local authentication is disabled and all other hosts use the hbac PAM.
