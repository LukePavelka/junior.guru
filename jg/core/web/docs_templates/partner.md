{% from 'macros.html' import lead, figure, partner_link with context %}

{% set active_partnership = partner.active_partnership() %}


# Partnerství s firmou {{ partner.name }}

{% call lead() %}
  Firma {{ partner.name }} je partnerem junior.guru od {{ '{:%-d.%-m.%Y}'.format(partner.first_partnership().starts_on) }}.
  Cílem tohoto přehledu je transparentně popsat, co je domluveno, a jak se to daří plnit.
  Díky tomu všichni vědí, jak na tom jsou. Tato stránka je veřejná, ale vyhledávačům není povoleno ji evidovat a zobrazovat.
{% endcall %}

{{ figure(partner.logo_path, partner.name, 500, 250, class="standout-bottom") }}

<div class="table-responsive"><table class="table table-1st-column-25">
  <tr>
    <th>Název</th>
    <td>{{ partner.name }}</td>
  </tr>
  <tr>
    <th>Odkaz</th>
    <td>{{ partner_link(partner.url, partner.url, 'open') }}</td>
  </tr>
  <tr>
    <th>Tarif</th>
    <td>
      {{ active_partnership.plan.name }}
      {%- for _ in range(active_partnership.plan.hierarchy_rank + 1) -%}
        &nbsp;{{- 'star'|icon -}}
      {%- endfor -%}<br>
      <small>{{ 'question-circle'|icon }} <a href="{{ pages|docs_url('pricing.md')|url }}">jak vypadá ceník</a></small>
    </td>
  </tr>
  <tr>
    <th>Prodloužení</th>
    <td>
      {% if active_partnership.expires_on %}
        Partnerství skončí za {{ active_partnership.days_until_expires() }} dní
        (do {{ '{:%-d.%-m.%Y}'.format(active_partnership.expires_on) }})
      {% else %}
        Partnerství nemá stanovený konec
      {% endif %}
    </td>
  </tr>
</table></div>


## Vztah s junior.guru

Veškerá placená spolupráce je viditelně označena.
{%- if partner.course_provider %}
Firma je **vzdělávací agenturou** a jako taková chce lidi přesvědčit o tom, že její vzdělávací programy jsou nejlepší.
Tím vzniká u Honzy Javorka, autora junior.guru, **konflikt zájmů** a proto se vztah s touto firmou řídí [opatrnějšími pravidly](../faq.md#vzdelavaci-agentury).
{% else %}
Firma nepodniká v oblasti vzdělávání juniorů a neměl by tedy existovat žádný konflikt zájmů, který by zpochybňoval neutralitu junior.guru.
{% endif %}

## Výsledky spolupráce

Pokud tady něco chybí, tak buď [nejde o placenou spolupráci](../faq.md#neoznacena-spoluprace), nebo to Honza zapomenul zaznamenat. Napiš mu na {{ 'honza@junior.guru'|email_link }}.

<div class="table-responsive"><table class="table table-1st-column-25">
  <tr>
    <th>Členů v klubu {{ 'person-circle'|icon }}</th>
    <td>
      {{ partner.list_members|length }} z 15<br>
      <small>{{ 'question-circle'|icon }} <a href="{{ pages|docs_url('faq.md')|url }}#firmy-klub">k čemu je členství</a></small>
    </td>
  </tr>

  {% for podcast_episode in partner.list_podcast_episodes %}
  <tr>
    <th>Epizoda podcastu {{ 'mic'|icon }}</th>
    <td><a href="{{ podcast_episode.url }}">{{ podcast_episode.format_title() }}</a></td>
  </tr>
  {% endfor %}

  {% for job in partner.list_jobs %}
  <tr>
    <th>Pracovní inzerát {{ 'pin-angle'|icon }}</th>
    <td>
      <a href="{{ job.url }}">{{ job.title }}</a><br>
      <small>
        {{ 'graph-up'|icon }} statistiky za
        <a href="{{ job.submitted_job.analytics_url(30) }}" target="_blank" rel="noopener">měsíc</a>,
        <a href="{{ job.submitted_job.analytics_url(365) }}" target="_blank" rel="noopener">rok</a>
      </small>
    </td>
  </tr>
  {% endfor %}

  {% for event in partner.list_events %}
  <tr>
    <th>Akce v klubu {{ 'calendar-event'|icon }}</th>
    <td><a href="{{ event.url }}">{{ event.title }}</a></td>
  </tr>
  {% endfor %}

  {% if partner.course_provider %}
  <tr>
    <th>Záznam v katalogu kurzů {{ 'star'|icon }}</th>
    <td>
      <a href="{{ pages|docs_url(partner.course_provider.page_url)|url }}">Kurzy od {{ partner.course_provider.name }}</a>
    </td>
  </tr>
  {% endif %}

  {% for benefit in active_partnership.evaluate_benefits(benefits_evaluators) %}
  {% if benefit.slug == 'welcome_social' and benefit.done %}
  <tr>
    <th>Oznámení na sociálních sítích {{ benefit.icon|icon }}</th>
    <td>
      <a href="{{ benefit.done }}">LinkedIn</a>
    </td>
  </tr>
  {% endif %}
  {% endfor %}

  {% set intro = partner.intro %}
  <tr>
    <th>Oznámení v klubu {{ 'balloon'|icon }}</th>
    <td>
      {% if intro %}
        <a href="{{ intro.url }}">{{ '{:%-d.%-m.%Y}'.format(intro.created_at) }}</a>
      {% else %}
        Objeví se každým dnem!
      {% endif %}
    </td>
  </tr>

  {% for partnership in partner.list_partnerships_history %}
    {% for agreement in partnership.agreements_registry|selectattr('done') %}
    <tr>
      <th>Další ujednání {{ 'box'|icon }}</th>
      <td>
        {{ agreement.text|md|remove_p }}
      </td>
    </tr>
    {% endfor %}
  {% endfor %}
</table></div>

## Stav benefitů

<div class="table-responsive"><table class="table table-1st-column-10">
{% for benefit in active_partnership.evaluate_benefits(benefits_evaluators) %}
<tr>
  {% if benefit.done %}
    <td class="text-success">{{ 'check-circle-fill'|icon }}</td>
  {% else %}
    <td class="text-danger">{{ 'x-circle'|icon }}</td>
  {% endif %}
  <td>
    {{ benefit.text|md|remove_p }}
    {{ benefit.icon|icon }}
  </td>
</tr>
{% endfor %}
</table></div>

{% if active_partnership.agreements_registry %}
### Další ujednání

<div class="table-responsive"><table class="table table-1st-column-10">
{% for agreement in active_partnership.agreements_registry %}
<tr>
  {% if agreement.done %}
    <td class="text-success">{{ 'check-circle-fill'|icon }}</td>
  {% else %}
    <td class="text-danger">{{ 'x-circle'|icon }}</td>
  {% endif %}
  <td>
    {{ agreement.text|md|remove_p }}
  </td>
</tr>
{% endfor %}
</table></div>
{% endif %}

## Historie

{% if partner.first_partnership().starts_on.year < 2022 %}
Partnerství jsou vždy na jeden rok. Do 2023 se však při prodlužování nedělal nový záznam, pouze se přepsalo datum ukončení.
{% endif %}

<div class="table-responsive"><table class="table">
  <tr>
    <th>Tarif</th>
    <th>Od</th>
    <th>Do</th>
  </tr>
{% for partnership in partner.list_partnerships_history %}
  <tr>
    <td>
      {% if partnership.plan %}
        {{ partnership.plan.name }}
      {% else %}
        (starý tarif, už neexistuje)
      {% endif %}
    </td>
    <td>{{ '{:%-d.%-m.%Y}'.format(partnership.starts_on) }}</td>
    <td>
      {% if partnership.expires_on %}
        {{ '{:%-d.%-m.%Y}'.format(partnership.expires_on) }}
      {% else %}
        ?
      {% endif %}
    </td>
  </tr>
{% endfor %}
</table></div>

<div class="pagination">
  <div class="pagination-control">
    <a href="{{ pages|docs_url('open.md')|url }}#firemni-partnerstvi" class="pagination-button">
      {{ 'arrow-left'|icon }}
      Všechna firemní partnerství
    </a>
  </div>
</div>
