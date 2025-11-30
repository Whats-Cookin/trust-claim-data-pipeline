from django.db import models


class Node(models.Model):
    """
    Maps to the existing Node table created by Prisma.
    managed = False means Django won't create/modify this table.
    """
    ENTITY_TYPES = [
        ('PERSON', 'Person'),
        ('ORGANIZATION', 'Organization'),
        ('CLAIM', 'Claim'),
        ('IMPACT', 'Impact'),
        ('EVENT', 'Event'),
        ('DOCUMENT', 'Document'),
        ('PRODUCT', 'Product'),
        ('PLACE', 'Place'),
        ('UNKNOWN', 'Unknown'),
        ('OTHER', 'Other'),
        ('CREDENTIAL', 'Credential'),
    ]

    id = models.AutoField(primary_key=True)
    nodeUri = models.CharField(max_length=2048, db_column='nodeUri')
    name = models.CharField(max_length=1024)
    entType = models.CharField(max_length=50, choices=ENTITY_TYPES, db_column='entType')
    descrip = models.TextField(blank=True, default='')
    image = models.CharField(max_length=2048, blank=True, null=True)
    thumbnail = models.CharField(max_length=2048, blank=True, null=True)
    # These fields will be added by Prisma migration
    editedAt = models.DateTimeField(blank=True, null=True, db_column='editedAt')
    editedBy = models.CharField(max_length=255, blank=True, null=True, db_column='editedBy')

    class Meta:
        managed = False
        db_table = 'Node'
        verbose_name = 'Node'
        verbose_name_plural = 'Nodes'

    def __str__(self):
        return f"{self.name} ({self.nodeUri[:50]})"


class Edge(models.Model):
    """
    Maps to the existing Edge table created by Prisma.
    Read-only in admin - edges should be created via claims.
    """
    id = models.AutoField(primary_key=True)
    startNode = models.ForeignKey(
        Node,
        on_delete=models.DO_NOTHING,
        related_name='edges_from',
        db_column='startNodeId'
    )
    endNode = models.ForeignKey(
        Node,
        on_delete=models.DO_NOTHING,
        related_name='edges_to',
        db_column='endNodeId',
        null=True,
        blank=True
    )
    label = models.CharField(max_length=255)
    thumbnail = models.CharField(max_length=2048, blank=True, null=True)
    claimId = models.IntegerField(db_column='claimId')

    class Meta:
        managed = False
        db_table = 'Edge'
        verbose_name = 'Edge'
        verbose_name_plural = 'Edges'

    def __str__(self):
        return f"{self.startNode_id} --{self.label}--> {self.endNode_id}"


class Claim(models.Model):
    """
    Maps to the existing Claim table. Read-only reference.
    """
    id = models.AutoField(primary_key=True)
    subject = models.CharField(max_length=2048)
    claim = models.CharField(max_length=255)
    object = models.CharField(max_length=2048, blank=True, null=True)
    statement = models.TextField(blank=True, null=True)
    effectiveDate = models.DateTimeField(blank=True, null=True, db_column='effectiveDate')
    sourceURI = models.CharField(max_length=2048, blank=True, null=True, db_column='sourceURI')
    createdAt = models.DateTimeField(db_column='createdAt')

    class Meta:
        managed = False
        db_table = 'Claim'
        verbose_name = 'Claim'
        verbose_name_plural = 'Claims'

    def __str__(self):
        return f"{self.subject[:30]} - {self.claim}"
