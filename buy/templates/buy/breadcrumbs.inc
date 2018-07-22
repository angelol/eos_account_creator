{% load i18n %}
<ul class="breadcrumbs">
  <li class="{% if breadcrumbs_account_name %}active{% endif %}{% if breadcrumbs_choose_finished%} finished{% endif %}"><a href="{% url 'choose' %}">{% trans "Choose Account Name" %}</a></li>
  <li class="{% if breadcrumbs_public_keys %}active{% endif %}{% if breadcrumbs_keys_finished%} finished{% endif %}"><a href="{% url 'keys' %}">{% trans "Provide Public Keys" %}</a></li>
  <li class="{% if breadcrumbs_payment %}active{% endif %}{% if breadcrumbs_purchase_finished%} finished{% endif %}"><a href="{% url 'purchase' %}">{% trans "Payment" %}</a></li>
</ul>