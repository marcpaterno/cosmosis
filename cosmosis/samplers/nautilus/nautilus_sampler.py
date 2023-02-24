from .. import ParallelSampler
import numpy as np
import sys
import os

def log_probability_function(p):
    r = pipeline.run_results(p)
    out = [r.post, r.prior]

    # Flatten any vector outputs here
    for e in r.extra:
        if np.isscalar(e):
            out.append(e)
        else:
            out.extend(e)
    out = tuple(out)
    return out


def prior_transform(p):
    return pipeline.denormalize_vector_from_prior(p)


class NautilusSampler(ParallelSampler):
    parallel_output = False
    internal_resume = True
    sampler_outputs = [ ('log_weight', float), ('prior', float), ("post", float)]

    def config(self):
        global pipeline
        pipeline = self.pipeline

        if self.is_master():
            self.n_live = self.read_ini("n_live", int, 1500)
            self.n_update = self.read_ini("n_update", int, self.n_live)
            self.enlarge = self.read_ini(
                "enlarge", float, 1.1**self.pipeline.nvaried)
            self.n_batch = self.read_ini("n_batch", int, 100)
            self.random_state = self.read_ini("random_state", int, -1)
            if self.random_state < 0:
                self.random_state = None
            self.resume_ = self.read_ini("resume", bool, False)
            self.f_live = self.read_ini("f_live", float, 0.01)
            self.n_shell = self.read_ini("n_shell", int, self.n_batch)
            self.n_eff = self.read_ini("n_eff", float, 10000.0)
            self.discard_exploration = self.read_ini(
                "discard_exploration", bool, False)
            self.verbose = self.read_ini("verbose", bool, False)

        self.converged = False

    def execute(self):
        from nautilus import Sampler

        n_dim = self.pipeline.nvaried

        try:
            resume_filepath = self.output.name_for_sampler_resume_info()
        except NotImplementedError:
            resume_filepath = None

        if resume_filepath is not None:
            resume_filepath = resume_filepath + ".hdf5"
            if self.resume_ and os.path.exists(resume_filepath):
                print(f"Resuming Nautilus from file {resume_filepath}")

        sampler = Sampler(
            prior_transform,
            log_probability_function,
            n_dim,
            n_live=self.n_live,
            n_update=self.n_update,
            enlarge=self.enlarge,
            n_batch=self.n_batch,
            random_state=self.random_state,
            filepath=resume_filepath,
            resume=self.resume_,
            pool=self.pool,
            blobs_dtype=float
        )

        sampler.run(f_live=self.f_live,
                    n_shell=self.n_shell,
                    n_eff=self.n_eff,
                    discard_exploration=self.discard_exploration,
                    verbose=self.verbose)

        for sample, logwt, logl, blob in zip(*sampler.posterior(return_blobs=True)):
            prior = blob[0]
            extra = blob[1:]
            logp = logl + prior
            self.output.parameters(sample, extra, logwt, prior, logp)

        self.output.final(
            "efficiency", sampler.effective_sample_size() / sampler.n_like)
        self.output.final("neff", sampler.effective_sample_size())
        self.output.final("nsample", len(sampler.posterior()[0]))
        self.output.final("log_z", sampler.evidence())
        self.converged = True

    def is_converged(self):
        return self.converged
