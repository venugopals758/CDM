from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
import xhtml2pdf.pisa as pisa
from django.views.decorators.csrf import csrf_exempt


class Render:
    @staticmethod
    def render(path, params, filename="document.pdf"):
        template = get_template(path)
        html = template.render(params)

        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        return HttpResponse("Error generating PDF", status=400)