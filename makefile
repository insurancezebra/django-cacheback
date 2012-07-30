puppet:
	# Install puppet modules required to set-up sandbox server
	puppet module install --target-dir sandbox/puppet/modules/ puppetlabs-rabbitmq -v 2.0.1
	puppet module install --target-dir sandbox/puppet/modules/ saz-memcached -v 2.0.2
	git clone git://github.com/uggedal/puppet-module-python.git sandbox/puppet/modules/python