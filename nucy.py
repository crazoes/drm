import random
from umbral import pre, keys, config, signing

config.set_default_curve()

class Alice:
    def __init__(self):
        self.alices_private_key = keys.UmbralPrivateKey.gen_key()
        self.alices_public_key = self.alices_private_key.get_pubkey()

        self.alices_signing_key = keys.UmbralPrivateKey.gen_key()
        self.alices_verifying_key = self.alices_signing_key.get_pubkey()
        self.alices_signer = signing.Signer(private_key=self.alices_signing_key)

    def encrypt(self, string):
        plaintext = string.encode() if isinstance(string, str) else string
        ciphertext, capsule = pre.encrypt(self.alices_public_key, plaintext)
        return ciphertext, capsule

    def decrypt(self, ciphertext, capsule):
        cleartext = pre.decrypt(ciphertext=ciphertext,
                                capsule=capsule,
                                decrypting_key=self.alices_private_key)
        return cleartext

    def genfrags(self, receiver, threshold=10, N=20):
        kfrags = pre.generate_kfrags(delegating_privkey=self.alices_private_key,
                                     signer=self.alices_signer,
                                     receiving_pubkey=receiver.bobs_public_key,
                                     threshold=threshold,
                                     N=N)
        import random
        return random.sample(kfrags, threshold)

class Bob:
    def __init__(self):
        self.bobs_private_key = keys.UmbralPrivateKey.gen_key()
        self.bobs_public_key = self.bobs_private_key.get_pubkey()
        self.capsule = None

    def setCapsule(self, capsule):
        self.capsule = capsule

    def decrypt(self, ciphertext):
        try:
            fail_decrypted_data = pre.decrypt(ciphertext=ciphertext,
                                              capsule=self.capsule,
                                              decrypting_key=self.bobs_private_key)
        except pre.UmbralDecryptionError:
            print("Decryption failed! Bob doesn't has access granted yet.")

    def setCorrectnessKeys(self, alice):
        self.capsule.set_correctness_keys(delegating=alice.alices_public_key,
                                         receiving=self.bobs_public_key,
                                         verifying=alice.alices_verifying_key)

    def decrypt(self, ciphertext, kfrags):
        cfrags = list()  # Bob's cfrag collection
        for kfrag in kfrags:
            cfrag = pre.reencrypt(kfrag=kfrag, capsule=self.capsule)
            cfrags.append(cfrag)  # Bob collects a cfrag

        
        for cfrag in cfrags:
            self.capsule.attach_cfrag(cfrag)


        bob_cleartext = pre.decrypt(ciphertext=ciphertext, capsule=self.capsule, decrypting_key=self.bobs_private_key)
        print(bob_cleartext)
        return bob_cleartext

class Seq:
    def __init__(self, content):
        self.content = content

    def start(self, cb=lambda x: print(x)):
        cb('generating server keys...')
        alice = Alice()

        cb('encrypting data...')
        cipher, capsule = alice.encrypt(self.content)
        yield cipher
        print(cipher)

        cb('pushing data to ipfs, transmitting fragments to nucypher...')

        cb('generating client keys...')
        bob = Bob()
        kfrags = alice.genfrags(bob)

        cb('getting data from ifps...')
        bob.setCapsule(capsule)

        cb('cant decrypt, getting re-encrypted...')
        bob.setCorrectnessKeys(alice)

        cb('decrypting re-encrypted content...')
        plain = bob.decrypt(cipher, kfrags)
        yield plain
        print(cipher)
        print(plain)
   
if __name__ == '__main__':
    a = Seq('Proxy Re-encryption is cool!')
    a.start()

    b = Seq(open('video.webm', 'rb').read())
    b.start()
