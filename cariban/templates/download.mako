<%inherit file="home_comp.mako"/>

<h3>${_('Downloads')}</h3>

<div class="alert alert-info">
    <p>
        This web application serves the latest
        ${h.external_link('https://github.com/cldf-datasets/mattercariban/releases', label=_('released version'))}
        of data curated at
        ${h.external_link('https://github.com/cldf-datasets/mattercariban', label='cldf-datasets/mattercariban')}.
        All released version are accessible via<br/>
        <a href="https://doi.org/10.5281/zenodo.4438188">
            <img src="https://zenodo.org/badge/DOI/10.5281/zenodo.4438188.svg" alt="DOI">
        </a>
        <br/>
        on ZENODO as well.
    </p>
</div>
