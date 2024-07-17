/*
 * Script to create the metrics models - node operators do not need to run this
 *
 */
import { Wallet } from '@ethersproject/wallet'
import { CeramicClient } from "@ceramicnetwork/http-client"
import { StreamID } from '@ceramicnetwork/streamid'
import { ModelInstanceDocument } from '@ceramicnetwork/stream-model-instance'

import { Ed25519Provider } from 'key-did-provider-ed25519'
import { DID } from 'dids'
import { getResolver } from 'key-did-resolver'
import { fromString } from 'uint8arrays'
import {readFileSync} from 'fs'

import { Cacao, SiweMessage } from '@didtools/cacao'

const CERAMIC_URL = process.env.CERAMIC_URL;
const ceramic = new CeramicClient(CERAMIC_URL);
const LC_MODEL=StreamID.fromString('kjzl6hvfrbw6c7f8zr4bdyzfumj7hv7r9i7dbu57isrzezqjuetkum2885p9agc')

const seed_str = 'bb61714d289ca92bcf6abf10abf58b80b5c7b2443406a0ac84bdaf5d322a4758';
const seed = Uint8Array.from(Buffer.from(seed_str, 'hex'));  // 32 bytes of entropy, Uint8Array
const provider = new Ed25519Provider(seed)
const wallet = Wallet.createRandom()
const address = wallet.address

const siwe = new SiweMessage({
  domain: 'live.linkedtrust.us',
  address: address,
  statement: 'I accept the LinkedTrust Terms of Service',
  uri: 'did:key:z6MkpNSVhkVy3WdVH77yiUiBrmt5mPjqe2CWPUZ6fNxVdemR',
//  uri: 'did:key:z6MkrBdNdwUPnXDVD1DCxedzVVBpaGi8aSmoXFAeKNgtAer8',
  version: '1',
  nonce: '32891757',
  issuedAt: '2021-09-30T16:25:24.000Z',
  chainId: '1',
  resources: [
    'ipfs://Qme7ss3ARVgxv6rXqVPiikMJ8u2NLgmgszg13pYrDKEoiu',
    'https://example.com/my-web2-claim.json',
    'ceramic://*?model=kjzl6hvfrbw6c7f8zr4bdyzfumj7hv7r9i7dbu57isrzezqjuetkum2885p9agc'
  ],
})


const authenticate = async () => {
  const seed = readFileSync("./admin_seed.txt", 'utf8').trim();
  const key = fromString(seed, "base16");
  const did = new DID({
    resolver: getResolver(),
    provider: new Ed25519Provider(key),
  });

  const signature = await wallet.signMessage(siwe.toMessage())
  siwe.signature = signature
  const cacao = Cacao.fromSiweMessage(siwe);

  const didWithCap = did.withCapability(cacao)

  await didWithCap.authenticate();
  ceramic.did = didWithCap;
  return didWithCap
};

(async () => {
  const did = await authenticate();

  const dataArgument = process.argv[2];
  const data = JSON.parse(dataArgument);
  const result = await ModelInstanceDocument.create(ceramic, data, { model: LC_MODEL})

  console.log(result.id.toString())
  //
})();
