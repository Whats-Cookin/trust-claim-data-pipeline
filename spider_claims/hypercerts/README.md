Raw notes:

Hypercerts
https://thegraph.com/hosted-service/subgraph/hypercerts-admin/hypercerts-optimism-mainnet
add 'uri' field to the claim query like
```
{
  allowlists(first: 5) {
    id
    root
    claim {
      id
    }
  }
  claims(first: 5) {
    id
    uri
    creation
    tokenID
    contract
  }
}
```
(do this programatically)


THEN
ipfs dag get ipfs://bafkreic5traeqomikw5bbug5mce56c33udser25cpyykoz3zmr6hggapfu
from the ones with uri field
THEN
parse the results usefully into things, keep all urls along the way
This will help us with filecoin green
